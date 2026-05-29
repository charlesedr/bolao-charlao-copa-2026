from sqlmodel import Session, select

from app.domain.models import Palpite, PontuacaoPartida


def get(session: Session, usuario_id: int, partida_id: int) -> Palpite | None:
    stmt = select(Palpite).where(
        Palpite.usuario_id == usuario_id, Palpite.partida_id == partida_id
    )
    return session.exec(stmt).first()


def listar_por_usuario(session: Session, usuario_id: int) -> list[Palpite]:
    stmt = select(Palpite).where(Palpite.usuario_id == usuario_id)
    return list(session.exec(stmt).all())


def listar_por_partida(session: Session, partida_id: int) -> list[Palpite]:
    stmt = select(Palpite).where(Palpite.partida_id == partida_id)
    return list(session.exec(stmt).all())


def pontuacao(session: Session, usuario_id: int, partida_id: int) -> PontuacaoPartida | None:
    stmt = select(PontuacaoPartida).where(
        PontuacaoPartida.usuario_id == usuario_id,
        PontuacaoPartida.partida_id == partida_id,
    )
    return session.exec(stmt).first()
