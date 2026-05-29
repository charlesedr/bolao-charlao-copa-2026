"""Ranking geral com critérios de desempate."""
from sqlalchemy import func
from sqlmodel import Session, select

from app.domain.enums import StatusUsuario
from app.domain.models import ApostaClassificacaoFinal, PontuacaoPartida, Usuario


def ranking(session: Session) -> list[dict]:
    soma_partidas = dict(
        session.exec(
            select(PontuacaoPartida.usuario_id, func.sum(PontuacaoPartida.pontos_total)).group_by(
                PontuacaoPartida.usuario_id
            )
        ).all()
    )
    exatos = dict(
        session.exec(
            select(
                PontuacaoPartida.usuario_id, func.sum(PontuacaoPartida.pontos_placar_exato)
            ).group_by(PontuacaoPartida.usuario_id)
        ).all()
    )
    soma_aposta = dict(
        session.exec(
            select(ApostaClassificacaoFinal.usuario_id, ApostaClassificacaoFinal.pontos_total)
        ).all()
    )

    usuarios = session.exec(
        select(Usuario).where(Usuario.status == StatusUsuario.APROVADO)
    ).all()

    linhas = []
    for u in usuarios:
        pontos = int(soma_partidas.get(u.id, 0) or 0) + int(soma_aposta.get(u.id, 0) or 0)
        linhas.append(
            {
                "usuario_id": u.id,
                "apelido": u.apelido,
                "nome": u.nome,
                "pontos": pontos,
                "placares_exatos": int(exatos.get(u.id, 0) or 0),
            }
        )
    # Desempate: pontos -> placares exatos -> apelido
    linhas.sort(key=lambda r: (-r["pontos"], -r["placares_exatos"], r["apelido"].lower()))
    for i, linha in enumerate(linhas, start=1):
        linha["posicao"] = i
    return linhas
