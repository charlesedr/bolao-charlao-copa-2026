from sqlalchemy import func, or_
from sqlmodel import Session, select

from app.domain.models import Usuario


def get_by_id(session: Session, usuario_id: int) -> Usuario | None:
    return session.get(Usuario, usuario_id)


def get_by_login(session: Session, login: str) -> Usuario | None:
    """Busca por apelido OU e-mail (case-insensitive)."""
    alvo = login.strip().lower()
    stmt = select(Usuario).where(
        or_(func.lower(Usuario.email) == alvo, func.lower(Usuario.apelido) == alvo)
    )
    return session.exec(stmt).first()


def get_by_email(session: Session, email: str) -> Usuario | None:
    stmt = select(Usuario).where(func.lower(Usuario.email) == email.strip().lower())
    return session.exec(stmt).first()


def get_by_apelido(session: Session, apelido: str) -> Usuario | None:
    stmt = select(Usuario).where(func.lower(Usuario.apelido) == apelido.strip().lower())
    return session.exec(stmt).first()


def listar(session: Session, status: str | None = None) -> list[Usuario]:
    stmt = select(Usuario).order_by(Usuario.created_at.desc())
    if status:
        stmt = stmt.where(Usuario.status == status)
    return list(session.exec(stmt).all())


def salvar(session: Session, usuario: Usuario) -> Usuario:
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario
