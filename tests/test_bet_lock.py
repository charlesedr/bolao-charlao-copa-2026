from datetime import UTC, datetime

from freezegun import freeze_time

from app.domain.enums import FasePartida
from app.domain.models import Partida
from app.services.bet_service import palpite_aberto

JOGO = datetime(2026, 6, 11, 19, 0, tzinfo=UTC)  # 16:00 BRT


def _partida(dt, fase=FasePartida.GRUPOS, mandante=1, visitante=2):
    return Partida(
        id=1, codigo="x", fase=fase, mandante_id=mandante, visitante_id=visitante, data_hora=dt
    )


@freeze_time("2026-06-11 18:54:00")  # 6 min antes
def test_aberto_seis_min_antes():
    assert palpite_aberto(_partida(JOGO)) is True


@freeze_time("2026-06-11 18:56:00")  # 4 min antes
def test_fechado_quatro_min_antes():
    assert palpite_aberto(_partida(JOGO)) is False


@freeze_time("2026-06-11 18:55:00")  # exatamente 5 min antes (prazo limite)
def test_no_limite_exato_fechado():
    # now == data_hora - 5min  → não é estritamente menor → fechado
    assert palpite_aberto(_partida(JOGO)) is False


@freeze_time("2026-06-11 20:00:00")  # jogo já começou
def test_fechado_apos_inicio():
    assert palpite_aberto(_partida(JOGO)) is False


@freeze_time("2026-06-01 12:00:00")
def test_mata_mata_sem_times_fechado():
    p = _partida(JOGO, fase=FasePartida.OITAVAS, mandante=None, visitante=None)
    assert palpite_aberto(p) is False
