from typing import List, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from cg.exc import CgError
from cg.store.models import Model

SESSION: Optional[scoped_session] = None
ENGINE: Optional[Engine] = None


def initialise_database(db_uri: str) -> None:
    """Initialize the global engine and session for SQLAlchemy."""
    global SESSION, ENGINE
    ENGINE = create_engine(db_uri, pool_pre_ping=True)
    session_factory = sessionmaker(ENGINE)
    SESSION = scoped_session(session_factory)


def get_session() -> Session:
    """
    Get a SQLAlchemy session with a connection to status db.
    The session is retrieved from the scoped session registry and is thread local.
    """
    if not SESSION:
        raise CgError("Database not initialised")
    return SESSION()


def get_scoped_session() -> Optional[scoped_session]:
    """Get the scoped session registry."""
    return SESSION


def get_engine() -> Engine:
    """Get the SQLAlchemy engine with a connection to status db."""
    if not ENGINE:
        raise CgError("Database not initialised")
    return ENGINE


def create_all_tables() -> None:
    """Create all tables in status db."""
    session: Session = get_session()
    Model.metadata.create_all(bind=session.get_bind())


def drop_all_tables() -> None:
    """Drop all tables in status db."""
    session: Session = get_session()
    Model.metadata.drop_all(bind=session.get_bind())


def get_tables() -> List[str]:
    """Get a list of all tables in status db."""
    engine: Engine = get_engine()
    return engine.table_names()
