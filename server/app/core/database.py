from collections.abc import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def tag_actor(session: Session, actor_id: str) -> None:
    """Name who is making this transaction's changes, for the audit trail (a transaction-local setting that
    the audit trigger reads). It disappears when the transaction ends, so it can never leak to another request."""
    session.execute(text("select set_config('app.actor_id', :id, true)"), {"id": actor_id})


def get_session() -> Iterator[Session]:
    """One session (= one transaction) per request."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
