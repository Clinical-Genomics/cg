from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from cg.exc import CgError
from cg.store.models import Model

SESSION: Optional[Session] = None
ENGINE = None


def initialise_database(db_uri: str):
    global SESSION, ENGINE
    ENGINE = create_engine(db_uri, pool_pre_ping=True)
    session_factory = sessionmaker(ENGINE)
    SESSION = scoped_session(session_factory)


def get_session() -> Session:
    if not SESSION:
        raise CgError("Database not initialised")
    return SESSION()


def get_engine():
    if not ENGINE:
        raise CgError("Database not initialised")
    return ENGINE


def create_all_tables() -> None:
    session: Session = get_session()
    Model.metadata.create_all(bind=session.get_bind())


def drop_all_tables() -> None:
    session: Session = get_session()
    Model.metadata.drop_all(bind=session.get_bind())


def get_tables() -> list:
    engine = get_engine()
    return engine.table_names()
