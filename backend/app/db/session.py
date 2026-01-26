import os

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")
DATABASE_ECHO = os.getenv("DATABASE_ECHO", False)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def SessionLocal():
    """Create a new SQLModel session"""
    return Session(engine)


def get_session():
    """Dependency for getting DB session"""
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


def init_db():
    """Create all tables"""
    SQLModel.metadata.create_all(engine)
