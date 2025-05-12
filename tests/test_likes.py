import pytest
from models import User, Photo, Like
from utils import hash_password
from auth import create_access_token
from sqlalchemy.orm import Session


@pytest.fixture
def test_user(db: Session):
    user = User(username="like_user", password=hash_password("pass"), role="User")
    photographer = User(username="like_photographer", password=hash_password("pass"), role="Photographer")
    db.add_all([user, photographer])
    db.commit()
    db.refresh(user)
    db.refresh(photographer)
    return {"user": user, "photographer": photographer}


@pytest.fixture
def auth_headers(test_user):
    # Token must include actual user ID or username to match auth logic
    user_token = create_access_token(data={"sub": test_user["user"].username})
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def photo_to_like(db: Session, test_user):
    photo = Photo(
        owner_id=test_user["photographer"].user_id,
        file_path="some_path.jpg",
        tags="test",
        description="test"
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo


def test_like_photo(client, auth_headers, photo_to_like):
    response = client.post(f"/likes/{photo_to_like.photo_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Photo liked successfully"


def test_like_photo_twice(client, auth_headers, photo_to_like):
    client.post(f"/likes/{photo_to_like.photo_id}", headers=auth_headers)
    response = client.post(f"/likes/{photo_to_like.photo_id}", headers=auth_headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "You have already liked this photo"


def test_unlike_photo(client, auth_headers, photo_to_like):
    client.post(f"/likes/{photo_to_like.photo_id}", headers=auth_headers)
    response = client.delete(f"/likes/{photo_to_like.photo_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Photo unliked successfully"


def test_unlike_photo_not_liked(client, auth_headers, photo_to_like):
    response = client.delete(f"/likes/{photo_to_like.photo_id}", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Like not found"


def test_get_like_count(client, auth_headers, photo_to_like):
    client.post(f"/likes/{photo_to_like.photo_id}", headers=auth_headers)
    response = client.get(f"/likes/{photo_to_like.photo_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["photo_id"] == photo_to_like.photo_id
    assert data["like_count"] == 1
