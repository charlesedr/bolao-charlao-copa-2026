from app.domain.models import PalpiteBracketSimulado
from app.services.bracket_sim_service import _vencedor_perdedor_sim, fase_completa


def _pal(vencedor_id: int) -> PalpiteBracketSimulado:
    return PalpiteBracketSimulado(
        usuario_id=1, partida_id=1, vencedor_id=vencedor_id,
        placar_vencedor=2, placar_perdedor=1,
    )


def test_vencedor_e_mandante():
    assert _vencedor_perdedor_sim(_pal(10), mandante_id=10, visitante_id=20) == (10, 20)


def test_vencedor_e_visitante():
    assert _vencedor_perdedor_sim(_pal(20), mandante_id=10, visitante_id=20) == (20, 10)


def test_vencedor_fora_do_confronto():
    # cascata quebrada: vencedor 99 não está em (10, 20)
    assert _vencedor_perdedor_sim(_pal(99), mandante_id=10, visitante_id=20) == (None, None)


def test_fase_completa_vazia_e_falsa():
    assert fase_completa([]) is False


def test_fase_completa_pendencia_e_falsa():
    items = [
        {"palpite": _pal(10), "dependencia_pendente": False},
        {"palpite": None, "dependencia_pendente": True},
    ]
    assert fase_completa(items) is False


def test_fase_completa_sem_palpite_e_falsa():
    items = [
        {"palpite": _pal(10), "dependencia_pendente": False},
        {"palpite": None, "dependencia_pendente": False},
    ]
    assert fase_completa(items) is False


def test_fase_completa_todos_palpitados_e_verdadeira():
    items = [
        {"palpite": _pal(10), "dependencia_pendente": False},
        {"palpite": _pal(20), "dependencia_pendente": False},
    ]
    assert fase_completa(items) is True
