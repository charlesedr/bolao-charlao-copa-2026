from sqlmodel import Session, select

from app.domain.models import Partida, Selecao


def get(session: Session, partida_id: int) -> Partida | None:
    return session.get(Partida, partida_id)


def listar(session: Session, fase: str | None = None) -> list[Partida]:
    stmt = select(Partida).order_by(Partida.data_hora)
    if fase:
        stmt = stmt.where(Partida.fase == fase)
    return list(session.exec(stmt).all())


def mapa_selecoes(session: Session) -> dict[int, Selecao]:
    return {s.id: s for s in session.exec(select(Selecao)).all()}
