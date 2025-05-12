import pytest
from models import User, Photo, Rating
from utils import hash_password
from auth import create_access_token
from sqlalchemy.orm import Session


@pytest.fixture
def test_user(db: Session):
    user = User(username="test_user", password=hash_password("password"))
    photographer = User(username="test_photographer",password=hash_password("password"), role="Photographer")
    db.add_all([user, photographer])
    db.commit()
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
def rated_photo(db: Session, test_user):
    photo = Photo(
        owner_id=test_user["photographer"].user_id,
        file_path="dummy_path.jpg",
        tags="nature",
        description="Sample"
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo


@pytest.fixture
def rated_photographer(db: Session, test_user):
    return test_user["photographer"]


def test_rate_photo(client, auth_headers, rated_photo):
    response = client.post(f"/ratings/photo/{rated_photo.photo_id}?rating=4", headers=auth_headers["user"])
    assert response.status_code == 200
    assert response.json()["message"] == "Photo rating updated"
    assert isinstance(response.json()["average_rating"], (int, float))

def test_get_photo_rating(client, auth_headers, rated_photo):
    # First rate it
    client.post(f"/ratings/photo/{rated_photo.photo_id}?rating=3", headers=auth_headers["user"])
    response = client.get(f"/ratings/photo/{rated_photo.photo_id}", headers=auth_headers["user"])
    assert response.status_code == 200
    assert "average_rating" in response.json()
    assert "user_rating" in response.json()

def test_delete_photo_rating(client, auth_headers, rated_photo):
    client.post(f"/ratings/photo/{rated_photo.photo_id}?rating=5", headers=auth_headers["user"])
    response = client.delete(f"/ratings/photo/{rated_photo.photo_id}", headers=auth_headers["user"])
    assert response.status_code == 200
    assert response.json()["message"] == "Photo rating deleted"

def test_rate_photographer(client, auth_headers, rated_photographer):
    response = client.post(f"/ratings/photographer/{rated_photographer.user_id}?rating=5", headers=auth_headers["user"])
    assert response.status_code == 200
    assert response.json()["message"] == "Photographer rating updated"

def test_get_photographer_rating(client, auth_headers, rated_photographer):
    client.post(f"/ratings/photographer/{rated_photographer.user_id}?rating=2", headers=auth_headers["user"])
    response = client.get(f"/ratings/photographer/{rated_photographer.user_id}", headers=auth_headers["user"])
    assert response.status_code == 200
    assert "average_rating" in response.json()
    assert "user_rating" in response.json()

def test_delete_photographer_rating(client, auth_headers, rated_photographer):
    client.post(f"/ratings/photographer/{rated_photographer.user_id}?rating=3", headers=auth_headers["user"])
    response = client.delete(f"/ratings/photographer/{rated_photographer.user_id}", headers=auth_headers["user"])
    assert response.status_code == 200
    assert response.json()["message"] == "Photographer rating deleted"

def test_invalid_photo_rating(client, auth_headers, rated_photo):
    response = client.post(f"/ratings/photo/{rated_photo.photo_id}?rating=6", headers=auth_headers["user"])
    assert response.status_code == 400
    assert "Rating must be between 1 and 5" in response.json()["detail"]

def test_invalid_photographer_rating(client, auth_headers, rated_photographer):
    response = client.post(f"/ratings/photographer/{rated_photographer.user_id}?rating=0", headers=auth_headers["user"])
    assert response.status_code == 400
    assert "Rating must be between 1 and 5" in response.json()["detail"]
