from app.services.standings_service import (
    LinhaClassificacao,
    classificar_grupo,
    melhores_terceiros,
)


def _ordem(jogos):
    return [linha.selecao_id for linha in classificar_grupo([1, 2, 3, 4], jogos)]


def test_ordem_por_pontos():
    jogos = [
        (1, 2, 1, 0), (1, 3, 1, 0), (1, 4, 1, 0),
        (2, 3, 1, 0), (2, 4, 1, 0), (3, 4, 1, 0),
    ]
    assert _ordem(jogos) == [1, 2, 3, 4]


def test_desempate_por_saldo():
    # 1 e 2 com 7 pts; 1 tem saldo melhor (+5 vs +2)
    jogos = [
        (1, 4, 4, 0), (1, 3, 1, 0), (1, 2, 0, 0),
        (2, 3, 1, 0), (2, 4, 1, 0), (3, 4, 1, 0),
    ]
    ordem = _ordem(jogos)
    assert ordem[0] == 1 and ordem[1] == 2


def test_desempate_por_confronto_direto():
    # 1 e 2 idênticos em pontos/saldo/gols; 1 venceu o confronto direto
    jogos = [
        (1, 2, 1, 0),  # 1 vence 2 (head-to-head)
        (3, 1, 1, 0),  # 3 vence 1
        (1, 4, 1, 0),  # 1 vence 4
        (2, 3, 1, 0),  # 2 vence 3
        (2, 4, 1, 0),  # 2 vence 4
        (3, 4, 0, 0),  # empate
    ]
    ordem = _ordem(jogos)
    assert ordem[0] == 1 and ordem[1] == 2  # 1 acima de 2 pelo confronto direto


def test_melhores_terceiros():
    terceiros = [
        LinhaClassificacao(selecao_id=10, pontos=4, gols_pro=5, gols_contra=3),  # +2
        LinhaClassificacao(selecao_id=11, pontos=4, gols_pro=3, gols_contra=2),  # +1
        LinhaClassificacao(selecao_id=12, pontos=3, gols_pro=6, gols_contra=1),  # +5
        LinhaClassificacao(selecao_id=13, pontos=6, gols_pro=2, gols_contra=2),  # 0
    ]
    top2 = melhores_terceiros(terceiros, qtd=2)
    assert [linha.selecao_id for linha in top2] == [13, 10]
