from datetime import UTC, datetime

from app.domain.enums import FasePartida, StatusPartida
from app.domain.models import Palpite, Partida
from app.services.simulation_service import _jogo_grupo_hibrido


def _partida(status=StatusPartida.NAO_INICIADO, placar_m=None, placar_v=None) -> Partida:
    return Partida(
        id=1,
        codigo="1",
        fase=FasePartida.GRUPOS,
        grupo_id=1,
        mandante_id=10,
        visitante_id=20,
        data_hora=datetime(2026, 6, 11, 19, tzinfo=UTC),
        status=status,
        placar_mandante=placar_m,
        placar_visitante=placar_v,
    )


def _palpite(gm=2, gv=2) -> Palpite:
    return Palpite(usuario_id=1, partida_id=1, gols_mandante=gm, gols_visitante=gv)


def test_jogo_hibrido_usa_oficial_finalizado():
    jogo, origem = _jogo_grupo_hibrido(
        _partida(StatusPartida.FINALIZADO, placar_m=1, placar_v=0),
        _palpite(3, 3),
    )

    assert jogo == (10, 20, 1, 0)
    assert origem == "oficial"


def test_jogo_hibrido_usa_palpite_se_nao_finalizado():
    jogo, origem = _jogo_grupo_hibrido(
        _partida(StatusPartida.EM_ANDAMENTO, placar_m=1, placar_v=0),
        _palpite(2, 1),
    )

    assert jogo == (10, 20, 2, 1)
    assert origem == "palpite"


def test_jogo_hibrido_fica_pendente_sem_palpite():
    jogo, origem = _jogo_grupo_hibrido(_partida(), None)

    assert jogo is None
    assert origem == "pendente"
