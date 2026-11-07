
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# SQLite database location
DATABASE_DIR = BASE_DIR / "data"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DATABASE_DIR / "ai_jobpilot.db"

# SQLite connection URL
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create database engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

# Create database session factory
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():
    """Provide a database session and close it safely."""
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
