from sqlmodel import Session, select

from app.domain.models import LogAdmin


def registrar(
    session: Session,
    *,
    admin_id: int,
    acao: str,
    entidade: str,
    entidade_id: int | None = None,
    detalhes: dict | None = None,
) -> None:
    session.add(
        LogAdmin(
            admin_id=admin_id,
            acao=acao,
            entidade=entidade,
            entidade_id=entidade_id,
            detalhes=detalhes,
        )
    )


def listar(session: Session, limite: int = 100) -> list[LogAdmin]:
    stmt = select(LogAdmin).order_by(LogAdmin.created_at.desc()).limit(limite)
    return list(session.exec(stmt).all())
