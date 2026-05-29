from datetime import datetime

import pytest

from app.domain.enums import FasePartida
from app.domain.models import ApostaClassificacaoFinal, Palpite, Partida
from app.services.scoring_service import (
    calcular_pontos_aposta_final,
    calcular_pontos_palpite,
    fair_play_points,
    pontuar,
)

HOME, AWAY = 1, 2
DUMMY_DT = datetime(2026, 6, 11, 19, 0, 0)


def _partida(fase, pm, pv, classificado_id=None):
    return Partida(
        id=1,
        codigo="X",
        fase=fase,
        mandante_id=HOME,
        visitante_id=AWAY,
        data_hora=DUMMY_DT,
        placar_mandante=pm,
        placar_visitante=pv,
        classificado_id=classificado_id,
    )


def _palpite(gm, gv, classificado_id=None):
    return Palpite(
        usuario_id=10, partida_id=1, gols_mandante=gm, gols_visitante=gv,
        classificado_id=classificado_id,
    )


# ---------------------------------------------------------------- Fase de grupos
@pytest.mark.parametrize(
    "gm_p,gv_p,gm_o,gv_o,esperado",
    [
        (1, 0, 1, 0, 5),  # placar exato
        (2, 0, 1, 0, 3),  # acerta vencedor + gols visitante
        (1, 1, 1, 0, 1),  # acerta só gols mandante
        (3, 1, 1, 0, 2),  # acerta só o resultado (vitória mandante)
        (0, 1, 1, 0, 0),  # erra tudo
        (0, 0, 1, 0, 1),  # acerta só gols visitante
        (2, 2, 2, 2, 5),  # empate exato
        (1, 1, 2, 2, 2),  # acerta resultado (empate)
        (0, 0, 2, 2, 2),  # acerta resultado (empate)
        (2, 1, 2, 2, 1),  # acerta só gols mandante
    ],
)
def test_pontuacao_fase_grupos(gm_p, gv_p, gm_o, gv_o, esperado):
    r = pontuar(
        gols_mandante_palpite=gm_p, gols_visitante_palpite=gv_p,
        gols_mandante_oficial=gm_o, gols_visitante_oficial=gv_o, is_mata_mata=False,
    )
    assert r.total == esperado


# ----------------------------------------------- Mata-mata (oficial 1x1, HOME passa)
@pytest.mark.parametrize(
    "gm,gv,classif,esperado",
    [
        (1, 1, HOME, 6),  # placar exato + acertou classificado
        (1, 1, AWAY, 5),  # placar exato, errou classificado
        (0, 0, HOME, 3),  # acertou empate + classificado
        (0, 0, AWAY, 2),  # acertou empate, errou classificado
        (2, 1, None, 2),  # previu vitória HOME (classif derivado=HOME) + gols visitante
        (1, 2, None, 1),  # previu vitória AWAY (classif AWAY) — só gols mandante
    ],
)
def test_mata_mata_oficial_empate_home_classifica(gm, gv, classif, esperado):
    partida = _partida(FasePartida.OITAVAS, 1, 1, classificado_id=HOME)
    palpite = _palpite(gm, gv, classificado_id=classif)
    assert calcular_pontos_palpite(palpite, partida).pontos_total == esperado


# ------------------------------------- Mata-mata (oficial 2x1, decidido em campo, HOME passa)
@pytest.mark.parametrize(
    "gm,gv,classif,esperado",
    [
        (2, 1, None, 6),  # placar exato + classificado derivado HOME
        (1, 1, HOME, 2),  # gols visitante + classificado (empate previsto, escolheu HOME)
        (3, 1, None, 4),  # resultado + gols visitante + classificado HOME
        (0, 2, None, 0),  # previu vitória AWAY — erra tudo
    ],
)
def test_mata_mata_oficial_decidido_campo(gm, gv, classif, esperado):
    partida = _partida(FasePartida.QUARTAS, 2, 1, classificado_id=None)  # deriva oficial=HOME
    palpite = _palpite(gm, gv, classificado_id=classif)
    assert calcular_pontos_palpite(palpite, partida).pontos_total == esperado


def test_sem_placar_oficial_retorna_zero():
    partida = _partida(FasePartida.GRUPOS, None, None)
    palpite = _palpite(2, 1)
    p = calcular_pontos_palpite(palpite, partida)
    assert p.pontos_total == 0


def test_grupos_ignora_classificado():
    partida = _partida(FasePartida.GRUPOS, 1, 1, classificado_id=HOME)
    palpite = _palpite(1, 1, classificado_id=HOME)
    p = calcular_pontos_palpite(palpite, partida)
    assert p.pontos_classificado == 0
    assert p.pontos_total == 5  # empate exato, sem bônus de classificado


# ---------------------------------------------------------------- Aposta final
def test_aposta_final_todos_acertos():
    ap = ApostaClassificacaoFinal(usuario_id=1, campeao_id=10, vice_id=20, terceiro_id=30, quarto_id=40)
    calcular_pontos_aposta_final(ap, campeao_id=10, vice_id=20, terceiro_id=30, quarto_id=40)
    assert ap.pontos_total == 4


def test_aposta_final_parcial():
    ap = ApostaClassificacaoFinal(usuario_id=1, campeao_id=10, vice_id=20, terceiro_id=30, quarto_id=40)
    calcular_pontos_aposta_final(ap, campeao_id=10, vice_id=99, terceiro_id=30, quarto_id=99)
    assert (ap.pontos_campeao, ap.pontos_vice, ap.pontos_terceiro, ap.pontos_quarto) == (1, 0, 1, 0)
    assert ap.pontos_total == 2


def test_aposta_final_zero():
    ap = ApostaClassificacaoFinal(usuario_id=1, campeao_id=1, vice_id=2, terceiro_id=3, quarto_id=4)
    calcular_pontos_aposta_final(ap, campeao_id=10, vice_id=20, terceiro_id=30, quarto_id=40)
    assert ap.pontos_total == 0


# ---------------------------------------------------------------- Fair play
def test_fair_play_points():
    # 3 amarelos + 1 vermelho direto = -3 -4 = -7
    assert fair_play_points(3, 0, 1, 0) == -7
    assert fair_play_points(0, 0, 0, 0) == 0
    assert fair_play_points(1, 1, 1, 1) == -13  # -1 -3 -4 -5
