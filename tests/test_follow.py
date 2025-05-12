import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from models import User, Follower
from utils import hash_password
from auth import create_access_token
from database import engine , SessionLocal,Base
from settings import settings

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup the test environment once per session"""
    # Ensure we're using the test database
    assert settings.ENV == "testing"
    
    # Create all tables at session start
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up at session end
    Base.metadata.drop_all(bind=engine)
@pytest.fixture(scope="function")
def db():
    """Create a fresh database session for each test with automatic rollback"""
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    
    yield session
    
    # Rollback and clean up after test
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def test_user(db):
    user = User(username="follow_user", password=hash_password("pass"))
    photographer = User(username="follow_photographer", password=hash_password("pass"), role="Photographer")
    db.add_all([user, photographer])
    db.commit()
    db.refresh(user)
    db.refresh(photographer)
    return {"user": user, "photographer": photographer}

@pytest.fixture
def auth_headers(test_user):
    user_token = create_access_token(data={"sub": test_user["user"].username})
    photographer_token = create_access_token(data={"sub": test_user["photographer"].username})
    return {
        "user": {"Authorization": f"Bearer {user_token}"},
        "photographer": {"Authorization": f"Bearer {photographer_token}"}
    }

@pytest.fixture
def followed_user(db, test_user):
    user = User(username="photog_to_follow", password=hash_password("pass"), role="Photographer")
    db.add(user)
    db.commit()
    db.refresh(user)

    follow = Follower(user_id=user.user_id, follower_id=test_user["user"].user_id)
    db.add(follow)
    db.commit()
    return user

def test_follow_user(client, auth_headers, db):
    new_photographer = User(username="new_photo", password=hash_password("pass"), role="Photographer")
    db.add(new_photographer)
    db.commit()
    db.refresh(new_photographer)

    response = client.post(f"/follow/{new_photographer.user_id}", headers=auth_headers["user"])
    assert response.status_code == 200
    assert "You are now following" in response.json()["detail"]

def test_unfollow_user(client, auth_headers, followed_user):
    response = client.delete(f"/follow/{followed_user.user_id}", headers=auth_headers["user"])
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully unfollowed."

def test_get_following(client, auth_headers, followed_user):
    response = client.get("/follow/following", headers=auth_headers["user"])
    assert response.status_code == 200
    assert any(u["user_id"] == followed_user.user_id for u in response.json()["users"])

def test_get_followers(client, auth_headers, test_user, followed_user):
    token = create_access_token(data={"sub": followed_user.username})
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/follow/followers", headers=headers)
    assert response.status_code == 200
    assert any(u["user_id"] == test_user["user"].user_id for u in response.json()["users"])
