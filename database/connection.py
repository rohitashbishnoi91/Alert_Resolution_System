"""
Database Connection and Session Management
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from database.models import Base
from contextlib import contextmanager

# Database configuration
DATABASE_URL = "sqlite:///./aars_database.db"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  
    echo=False 
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")


def drop_db():
    """Drop all database tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)
    print("✓ Database tables dropped")


def get_db() -> Session:
    """
    Dependency for FastAPI endpoints
    Yields a database session and closes it after use
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session():
    """
    Context manager for database sessions
    Usage: with get_db_session() as db:
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

