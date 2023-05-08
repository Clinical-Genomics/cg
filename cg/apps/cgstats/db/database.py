from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import scoped_session, Session, sessionmaker

from cg.apps.cgstats.db.models.base import Base


SESSION_FACTORY: Optional[Session] = None


def initialise_engine_and_session_factory(
    url: Optional[str] = None,
) -> None:
    """Initialize the global engine and SESSION_FACTORY for SQLAlchemy."""
    global SESSION_FACTORY

    if SESSION_FACTORY is not None:
        return

    if url is not None:
        engine = create_engine(url)
    else:
        raise ValueError("Must specify `url`.")

    SESSION_FACTORY = scoped_session(sessionmaker(bind=engine))


def get_session() -> Session:
    """Fetch a SQLAlchemy session with a connection to a DB."""
    global SESSION_FACTORY
    assert SESSION_FACTORY is not None
    return SESSION_FACTORY()


def create_all_tables(engine: Engine) -> None:
    Base.metadata.create_all(engine)


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def initialise_test_engine_and_session_factory() -> None:
    """Initialize the global engine and SESSION_FACTORY for SQLAlchemy,
    using an in-memory SQLite database."""
    global SESSION_FACTORY

    engine = create_test_engine()
    create_all_tables(engine)

    SESSION_FACTORY = scoped_session(sessionmaker(bind=engine))


def create_test_engine() -> Engine:
    """Creates an in memory SQLAlchemy engine object for use in unit tests."""
    db_path = "sqlite://"
    return create_engine(db_path)
