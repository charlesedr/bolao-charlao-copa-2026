"""Classificação de grupos da Copa com critérios oficiais de desempate da FIFA (1-6).

Funções puras sobre primitivos — servem tanto para a Copa Real (placares oficiais)
quanto para a "Minha Copa" (palpites do usuário).

Critérios (G.5.3):
  1. Pontos (todos os jogos do grupo)
  2. Saldo de gols (todos os jogos)
  3. Gols pró (todos os jogos)
  4. Pontos no confronto direto entre os empatados
  5. Saldo de gols no confronto direto
  6. Gols pró no confronto direto
  (7 = fair play e 8 = sorteio são resolvidos fora daqui, por intervenção do admin
   ou desempate manual do usuário.)
"""
from dataclasses import dataclass

# Um jogo é uma tupla: (mandante_id, visitante_id, gols_mandante, gols_visitante)
Jogo = tuple[int, int, int, int]


@dataclass
class LinhaClassificacao:
    selecao_id: int
    pontos: int = 0
    jogos: int = 0
    vitorias: int = 0
    empates: int = 0
    derrotas: int = 0
    gols_pro: int = 0
    gols_contra: int = 0

    @property
    def saldo(self) -> int:
        return self.gols_pro - self.gols_contra


def _stats(times: list[int], jogos: list[Jogo]) -> dict[int, LinhaClassificacao]:
    tabela = {t: LinhaClassificacao(selecao_id=t) for t in times}
    for mand, vis, gm, gv in jogos:
        if mand not in tabela or vis not in tabela:
            continue
        m, v = tabela[mand], tabela[vis]
        m.jogos += 1
        v.jogos += 1
        m.gols_pro += gm
        m.gols_contra += gv
        v.gols_pro += gv
        v.gols_contra += gm
        if gm > gv:
            m.pontos += 3
            m.vitorias += 1
            v.derrotas += 1
        elif gv > gm:
            v.pontos += 3
            v.vitorias += 1
            m.derrotas += 1
        else:
            m.pontos += 1
            v.pontos += 1
            m.empates += 1
            v.empates += 1
    return tabela


def _chave_geral(linha: LinhaClassificacao) -> tuple[int, int, int]:
    return (linha.pontos, linha.saldo, linha.gols_pro)


def _ordenar_confronto_direto(empatados: list[int], jogos: list[Jogo]) -> list[int]:
    """Critérios 4-6: mini-tabela considerando apenas jogos entre os empatados."""
    sub = [
        (m, v, gm, gv)
        for (m, v, gm, gv) in jogos
        if m in empatados and v in empatados
    ]
    mini = _stats(empatados, sub)
    return sorted(empatados, key=lambda t: _chave_geral(mini[t]), reverse=True)


def classificar_grupo(times: list[int], jogos: list[Jogo]) -> list[LinhaClassificacao]:
    """Retorna as linhas da classificação ordenadas do 1º ao último.

    Aplica critérios 1-3 sobre todos os jogos e, para empates remanescentes,
    critérios 4-6 (confronto direto). Empates ainda persistentes mantêm ordem
    estável por selecao_id (placeholder para fair play/sorteio/manual).
    """
    tabela = _stats(times, jogos)

    # Ordenação inicial por critérios 1-3
    ordem = sorted(times, key=lambda t: _chave_geral(tabela[t]), reverse=True)

    # Resolve blocos empatados em (pontos, saldo, gols_pro) via confronto direto
    resultado: list[int] = []
    i = 0
    while i < len(ordem):
        j = i + 1
        while j < len(ordem) and _chave_geral(tabela[ordem[j]]) == _chave_geral(tabela[ordem[i]]):
            j += 1
        bloco = ordem[i:j]
        if len(bloco) > 1:
            bloco = _ordenar_confronto_direto(bloco, jogos)
            # desempate final determinístico (placeholder p/ fair play/sorteio)
            bloco = sorted(bloco, key=lambda t: (_ordem_cd_rank(t, bloco), t))
        resultado.extend(bloco)
        i = j

    return [tabela[t] for t in resultado]


def _ordem_cd_rank(time: int, bloco_ordenado: list[int]) -> int:
    return bloco_ordenado.index(time)


def melhores_terceiros(
    terceiros: list[LinhaClassificacao], qtd: int = 8
) -> list[LinhaClassificacao]:
    """Ranqueia os 3º colocados (critérios 1-3) e retorna os `qtd` melhores.

    FIFA não usa confronto direto entre 3º colocados (eles não se enfrentaram).
    Empates remanescentes (fair play/sorteio) ficam para intervenção do admin.
    """
    ordenados = sorted(
        terceiros, key=lambda x: (x.pontos, x.saldo, x.gols_pro, -x.selecao_id), reverse=True
    )
    return ordenados[:qtd]
