"""Testes do results_sync_service — parsing puro, sem HTTP."""
from app.services.results_sync_service import _contar_cartoes, _parse_evento


def _evento(status_completed: bool, m_abbr: str, m_score: str, v_abbr: str, v_score: str):
    return {
        "id": "660001",
        "status": {"type": {"completed": status_completed, "state": "post"}},
        "competitions": [{
            "competitors": [
                {
                    "homeAway": "home",
                    "team": {"id": "205", "abbreviation": m_abbr},
                    "score": m_score,
                },
                {
                    "homeAway": "away",
                    "team": {"id": "350", "abbreviation": v_abbr},
                    "score": v_score,
                },
            ]
        }],
    }


def test_parse_finalizado():
    p = _parse_evento(_evento(True, "BRA", "2", "MAR", "1"))
    assert p["completed"] is True
    assert p["mandante_abbr"] == "BRA"
    assert p["visitante_abbr"] == "MAR"
    assert p["placar_mandante"] == 2
    assert p["placar_visitante"] == 1


def test_parse_em_andamento_nao_completo():
    p = _parse_evento(_evento(False, "ARG", "0", "ESP", "0"))
    assert p["completed"] is False


def test_parse_placar_invalido_vira_none():
    p = _parse_evento(_evento(True, "BRA", "x", "MAR", ""))
    assert p["placar_mandante"] is None
    assert p["placar_visitante"] is None


def test_parse_sem_competicoes_retorna_none():
    assert _parse_evento({"id": "1", "status": {"type": {"completed": True}}}) is None


def test_contar_cartoes_classifica_yellow_red_e_red_separadamente():
    summary = {"keyEvents": [
        {"type": {"text": "Yellow Card"}, "team": {"id": "205"}},
        {"type": {"text": "Yellow Card"}, "team": {"id": "205"}},
        {"type": {"text": "Red Card"}, "team": {"id": "350"}},
        {"type": {"text": "Yellow Red Card"}, "team": {"id": "205"}},
        {"type": {"text": "Second Yellow Card"}, "team": {"id": "350"}},
    ]}
    c = _contar_cartoes(summary)
    assert c["205"]["amarelos"] == 2
    assert c["205"]["verm_2amarelo"] == 1
    assert c["205"]["verm_direto"] == 0
    assert c["350"]["amarelos"] == 0
    assert c["350"]["verm_2amarelo"] == 1
    assert c["350"]["verm_direto"] == 1


def test_contar_cartoes_evento_sem_team_e_ignorado():
    summary = {"keyEvents": [
        {"type": {"text": "Yellow Card"}, "team": {}},
        {"type": {"text": "Red Card"}},
    ]}
    assert _contar_cartoes(summary) == {}


def test_contar_cartoes_payload_vazio():
    assert _contar_cartoes({}) == {}
