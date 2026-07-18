from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker


class Base(DeclarativeBase):
    pass


def make_session_factory(database_url: str):
    engine = create_engine(database_url, pool_pre_ping=True)
    session_factory = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))
    return engine, session_factory
