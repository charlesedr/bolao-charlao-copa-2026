"""Ranking geral com critérios de desempate."""
from sqlalchemy import func
from sqlmodel import Session, select

from app.domain.enums import StatusUsuario
from app.domain.models import ApostaClassificacaoFinal, PontuacaoPartida, Usuario


def ranking(session: Session) -> list[dict]:
    # Agregados por usuário a partir da pontuação das partidas
    agregados = session.exec(
        select(
            PontuacaoPartida.usuario_id,
            func.sum(PontuacaoPartida.pontos_total),
            func.sum(PontuacaoPartida.pontos_placar_exato),
            func.sum(PontuacaoPartida.pontos_resultado),
            func.sum(
                PontuacaoPartida.pontos_gols_mandante + PontuacaoPartida.pontos_gols_visitante
            ),
        ).group_by(PontuacaoPartida.usuario_id)
    ).all()

    pts_part, exatos, result_pts, gols = {}, {}, {}, {}
    for uid, total, ex, res, gl in agregados:
        pts_part[uid] = int(total or 0)
        exatos[uid] = int(ex or 0)
        result_pts[uid] = int(res or 0)  # 2 pontos por resultado acertado
        gols[uid] = int(gl or 0)         # 1 ponto por gol (mandante/visitante) acertado

    pts_aposta = dict(
        session.exec(
            select(ApostaClassificacaoFinal.usuario_id, ApostaClassificacaoFinal.pontos_total)
        ).all()
    )

    usuarios = session.exec(
        select(Usuario).where(Usuario.status == StatusUsuario.APROVADO).order_by(Usuario.id)
    ).all()

    linhas = []
    for u in usuarios:
        linhas.append(
            {
                "usuario_id": u.id,
                "apelido": u.apelido,
                "nome": u.nome,
                "pontos": pts_part.get(u.id, 0) + int(pts_aposta.get(u.id, 0) or 0),
                "placares_exatos": exatos.get(u.id, 0),
                "resultados": result_pts.get(u.id, 0) // 2,  # quantidade de resultados acertados
                "gols": gols.get(u.id, 0),                   # quantidade de gols acertados
            }
        )

    # Desempate: pontos -> placares exatos -> resultados -> gols.
    # Sem critério final por apelido: empate total = MESMA posição (1º, 2º, 2º, 4º...).
    linhas.sort(
        key=lambda r: (-r["pontos"], -r["placares_exatos"], -r["resultados"], -r["gols"])
    )
    posicao = 0
    chave_anterior = None
    for i, linha in enumerate(linhas):
        chave = (linha["pontos"], linha["placares_exatos"], linha["resultados"], linha["gols"])
        if chave != chave_anterior:
            posicao = i + 1
            chave_anterior = chave
        linha["posicao"] = posicao
    return linhas
