# database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from settings import settings

Base = declarative_base()

# Detect if we are running in a testing environment
if settings.ENV == "testing":
    DATABASE_URL = "sqlite:///:memory:"  # Use in-memory for isolated tests
    connect_args = {"check_same_thread": False}
    auto_create_tables = True
else:
    DATABASE_URL = settings.DATABASE_URL
    connect_args = {}
    auto_create_tables = False

# Set up SQLAlchemy engine and session
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Create tables if using SQLite in-memory (useful for tests)
if auto_create_tables:
    Base.metadata.create_all(bind=engine)

# Dependency override for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
