from sqlalchemy import create_engine, inspect
from sqlalchemy.engine.base import Engine
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from cg.exc import CgError
from cg.store.models import Base

SESSION: scoped_session | None = None
ENGINE: Engine | None = None


def initialize_database(db_uri: str) -> None:
    """Initialize the SQLAlchemy engine and session for status db."""
    global SESSION, ENGINE

    ENGINE = create_engine(db_uri, pool_pre_ping=True)
    session_factory = sessionmaker(ENGINE)
    SESSION = scoped_session(session_factory)


def get_session() -> Session:
    """Get a SQLAlchemy session with a connection to status db."""
    if not SESSION:
        raise CgError("Database not initialised")
    return SESSION


def get_scoped_session_registry() -> scoped_session | None:
    """Get the scoped session registry for status db."""
    return SESSION


def get_engine() -> Engine:
    """Get the SQLAlchemy engine with a connection to status db."""
    if not ENGINE:
        raise CgError("Database not initialised")
    return ENGINE


def create_all_tables() -> None:
    """Create all tables in status db."""
    session: Session = get_session()
    Base.metadata.create_all(bind=session.get_bind())


def drop_all_tables() -> None:
    """Drop all tables in status db."""
    session: Session = get_session()
    Base.metadata.drop_all(bind=session.get_bind())


def get_tables() -> list[str]:
    """Get a list of all tables in status db."""
    engine: Engine = get_engine()
    inspector: Inspector = inspect(engine)
    return inspector.get_table_names()
