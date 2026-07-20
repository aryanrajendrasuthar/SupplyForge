from sqlalchemy import create_engine
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker


class Base(DeclarativeBase):
    pass


def make_session_factory(database_url: str):
    engine = create_engine(database_url, pool_pre_ping=True)
    session_factory = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))
    return engine, session_factory


def create_all_safely(engine) -> None:
    """Base.metadata.create_all() isn't atomic against concurrent callers on
    SQL Server (no native CREATE TABLE IF NOT EXISTS) — this service's web
    process and its consumer process both call this on startup, and both can
    pass the checkfirst existence check before either issues CREATE TABLE.
    Losing that race is fine: the winner already created the schema."""
    try:
        Base.metadata.create_all(engine)
    except DBAPIError as exc:
        if "already an object named" not in str(exc.orig):
            raise
