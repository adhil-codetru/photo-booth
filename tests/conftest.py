import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dependencies import get_db
from database import Base
from main import app
from fastapi.testclient import TestClient
import models  # Import the models to ensure they're registered with Base

DATABASE_URL = "sqlite:///:memory:"

# Session-wide engine
@pytest.fixture(scope="session")
def engine():
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield engine
    # Clean up after tests
    Base.metadata.drop_all(bind=engine)

# Function-scoped DB session
@pytest.fixture(scope="function")
def db(engine):
    SessionLocal = sessionmaker(bind=engine)
    connection = engine.connect()
    # Begin a non-ORM transaction
    transaction = connection.begin()
    db = SessionLocal(bind=connection)

    try:
        yield db
    finally:
        db.close()
        # Roll back the transaction
        transaction.rollback()
        connection.close()

# Function-scoped FastAPI test client
@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass  # Don't close here as it's handled by the db fixture
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()