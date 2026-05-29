from datetime import datetime

from app.domain.enums import FasePartida
from app.domain.models import Partida
from app.services.bracket_service import vencedor_perdedor

DT = datetime(2026, 7, 4, 18, 0)


def _p(pm, pv, classif=None):
    return Partida(
        id=1, codigo="x", fase=FasePartida.OITAVAS, mandante_id=1, visitante_id=2,
        data_hora=DT, placar_mandante=pm, placar_visitante=pv, classificado_id=classif,
    )


def test_vencedor_mandante():
    assert vencedor_perdedor(_p(2, 1)) == (1, 2)


def test_vencedor_visitante():
    assert vencedor_perdedor(_p(0, 1)) == (2, 1)


def test_empate_classificado_mandante():
    assert vencedor_perdedor(_p(1, 1, classif=1)) == (1, 2)


def test_empate_classificado_visitante():
    assert vencedor_perdedor(_p(1, 1, classif=2)) == (2, 1)


def test_empate_sem_classificado():
    assert vencedor_perdedor(_p(1, 1)) == (None, None)


def test_sem_placar():
    assert vencedor_perdedor(_p(None, None)) == (None, None)
