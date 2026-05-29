from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine
from sqlmodel import Session, create_engine

from app.core.config import settings

engine: Engine = create_engine(settings.active_database_url, pool_pre_ping=True)


@contextmanager
def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
