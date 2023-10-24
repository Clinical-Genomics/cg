from typing import List, Optional

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine.base import Engine
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from cg.exc import CgError
from cg.store.models import Model

SESSION: Optional[scoped_session] = None
ENGINE: Optional[Engine] = None


def initialize_database(db_uri: str) -> None:
    """Initialize the SQLAlchemy engine and session for status db."""
    global SESSION, ENGINE
    ENGINE = create_engine(db_uri, pool_pre_ping=True, future=True)
    session_factory = sessionmaker(ENGINE)
    SESSION = scoped_session(session_factory)


def get_session() -> Session:
    """Get a SQLAlchemy session with a connection to status db."""
    if not SESSION:
        raise CgError("Database not initialised")
    return SESSION


def get_scoped_session_registry() -> Optional[scoped_session]:
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
    Model.metadata.create_all(bind=session.get_bind())


def drop_all_tables() -> None:
    """Drop all tables in status db."""
    session: Session = get_session()
    Model.metadata.drop_all(bind=session.get_bind())


def get_tables() -> List[str]:
    """Get a list of all tables in status db."""
    engine: Engine = get_engine()
    inspector: Inspector = inspect(engine)
    return inspector.get_table_names()
