"""Cálculo de pontuação do bolão — funções puras e testáveis (sem dependência de banco).

Regras (Entregável H):
- Fase de grupos (máx 5): +1 gols mandante, +1 gols visitante, +2 resultado, +1 placar exato.
- Mata-mata (máx 6): base 5 + 1 por acertar quem se classifica (sempre, não só em empate).
  O placar conta APENAS os 90 minutos; prorrogação/pênaltis só definem o classificado.
- Aposta final (máx 4): +1 por posição (campeão, vice, 3º, 4º).
"""
from dataclasses import dataclass

from app.domain.enums import FasePartida
from app.domain.models import ApostaClassificacaoFinal, Palpite, Partida, PontuacaoPartida


def _sinal(a: int, b: int) -> int:
    """1 = vitória mandante, 0 = empate, -1 = vitória visitante."""
    if a > b:
        return 1
    if a < b:
        return -1
    return 0


@dataclass
class ResultadoPontuacao:
    pontos_gols_mandante: int = 0
    pontos_gols_visitante: int = 0
    pontos_resultado: int = 0
    pontos_placar_exato: int = 0
    pontos_classificado: int = 0

    @property
    def total(self) -> int:
        return (
            self.pontos_gols_mandante
            + self.pontos_gols_visitante
            + self.pontos_resultado
            + self.pontos_placar_exato
            + self.pontos_classificado
        )


def pontuar(
    *,
    gols_mandante_palpite: int,
    gols_visitante_palpite: int,
    gols_mandante_oficial: int,
    gols_visitante_oficial: int,
    is_mata_mata: bool = False,
    classificado_palpite_id: int | None = None,
    classificado_oficial_id: int | None = None,
) -> ResultadoPontuacao:
    """Núcleo puro de pontuação a partir de valores primitivos."""
    r = ResultadoPontuacao()

    if gols_mandante_palpite == gols_mandante_oficial:
        r.pontos_gols_mandante = 1
    if gols_visitante_palpite == gols_visitante_oficial:
        r.pontos_gols_visitante = 1
    if _sinal(gols_mandante_palpite, gols_visitante_palpite) == _sinal(
        gols_mandante_oficial, gols_visitante_oficial
    ):
        r.pontos_resultado = 2
    if (
        gols_mandante_palpite == gols_mandante_oficial
        and gols_visitante_palpite == gols_visitante_oficial
    ):
        r.pontos_placar_exato = 1

    if (
        is_mata_mata
        and classificado_palpite_id is not None
        and classificado_oficial_id is not None
        and classificado_palpite_id == classificado_oficial_id
    ):
        r.pontos_classificado = 1

    return r


def calcular_pontos_palpite(palpite: Palpite, partida: Partida) -> PontuacaoPartida:
    """Aplica a pontuação a um palpite contra o resultado oficial de uma partida.

    Para mata-mata, o "classificado previsto" é derivado: vencedor do placar palpitado
    quando não-empate, ou o time escolhido explicitamente quando empate. Idem para o oficial.
    """
    base = PontuacaoPartida(usuario_id=palpite.usuario_id, partida_id=partida.id or 0)

    if partida.placar_mandante is None or partida.placar_visitante is None:
        return base  # jogo sem placar oficial → 0

    is_mata_mata = partida.fase != FasePartida.GRUPOS

    classificado_palpite = palpite.classificado_id
    classificado_oficial = partida.classificado_id
    if is_mata_mata:
        if palpite.gols_mandante != palpite.gols_visitante:
            classificado_palpite = (
                partida.mandante_id
                if palpite.gols_mandante > palpite.gols_visitante
                else partida.visitante_id
            )
        if partida.placar_mandante != partida.placar_visitante:
            classificado_oficial = (
                partida.mandante_id
                if partida.placar_mandante > partida.placar_visitante
                else partida.visitante_id
            )

    r = pontuar(
        gols_mandante_palpite=palpite.gols_mandante,
        gols_visitante_palpite=palpite.gols_visitante,
        gols_mandante_oficial=partida.placar_mandante,
        gols_visitante_oficial=partida.placar_visitante,
        is_mata_mata=is_mata_mata,
        classificado_palpite_id=classificado_palpite,
        classificado_oficial_id=classificado_oficial,
    )

    base.pontos_gols_mandante = r.pontos_gols_mandante
    base.pontos_gols_visitante = r.pontos_gols_visitante
    base.pontos_resultado = r.pontos_resultado
    base.pontos_placar_exato = r.pontos_placar_exato
    base.pontos_classificado = r.pontos_classificado
    base.pontos_total = r.total
    return base


def calcular_pontos_aposta_final(
    aposta: ApostaClassificacaoFinal,
    *,
    campeao_id: int | None,
    vice_id: int | None,
    terceiro_id: int | None,
    quarto_id: int | None,
) -> ApostaClassificacaoFinal:
    aposta.pontos_campeao = 1 if campeao_id and aposta.campeao_id == campeao_id else 0
    aposta.pontos_vice = 1 if vice_id and aposta.vice_id == vice_id else 0
    aposta.pontos_terceiro = 1 if terceiro_id and aposta.terceiro_id == terceiro_id else 0
    aposta.pontos_quarto = 1 if quarto_id and aposta.quarto_id == quarto_id else 0
    aposta.pontos_total = (
        aposta.pontos_campeao
        + aposta.pontos_vice
        + aposta.pontos_terceiro
        + aposta.pontos_quarto
    )
    return aposta


def fair_play_points(
    amarelos: int, verm_2amarelo: int, verm_direto: int, amarelo_verm: int
) -> int:
    """Pontos de fair play da FIFA (critério 7 de desempate). Menos negativo = melhor."""
    return -1 * amarelos - 3 * verm_2amarelo - 4 * verm_direto - 5 * amarelo_verm
