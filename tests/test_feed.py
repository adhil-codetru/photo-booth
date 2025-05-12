import pytest
from models import User, Photo, Follower, Like
from utils import hash_password
from auth import create_access_token
from sqlalchemy.orm import Session
from unittest.mock import patch

@pytest.fixture
def feed_users(db: Session):
    user = User(username="feed_user", password=hash_password("pass"), role="User")
    photographer = User(username="feed_photographer", password=hash_password("pass"), role="Photographer")
    db.add_all([user, photographer])
    db.commit()
    db.refresh(user)
    db.refresh(photographer)
    return {"user": user, "photographer": photographer}

@pytest.fixture
def feed_auth_headers(feed_users):
    user_token = create_access_token(data={"sub": feed_users["user"].username})
    return {"Authorization": f"Bearer {user_token}"}

@pytest.fixture
def followed_photos(db: Session, feed_users):
    # User follows photographer
    follow = Follower(user_id=feed_users["photographer"].user_id, follower_id=feed_users["user"].user_id)
    db.add(follow)
    db.commit()

    # Add photos
    photo1 = Photo(
        owner_id=feed_users["photographer"].user_id,
        file_path="fake1.jpg",
        tags="ai-tag-1",  # Normally classified
        description="ai-description-1",  # Normally described
        average_rating=4.5
    )
    photo2 = Photo(
        owner_id=feed_users["photographer"].user_id,
        file_path="fake2.jpg",
        tags="ai-tag-2",
        description="ai-description-2",
        average_rating=3.8
    )
    db.add_all([photo1, photo2])
    db.commit()
    db.refresh(photo1)
    db.refresh(photo2)

    # Add likes to make photo2 the photo of the day
    like = Like(user_id=feed_users["user"].user_id, photo_id=photo2.photo_id)
    db.add(like)
    db.commit()

    return [photo1, photo2]

@patch("routes.photo.classify_image", return_value="mocked-nature")
@patch("routes.photo.describe_image", return_value="mocked-description")
def test_get_feed_photos(mock_describe, mock_classify, client, feed_auth_headers, followed_photos):
    """Test that user receives feed photos from followed photographers"""
    response = client.get("/feed/", headers=feed_auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert "feed_photos" in data
    assert len(data["feed_photos"]) == 2

    photo_ids = [p["photo_id"] for p in data["feed_photos"]]
    assert all(photo.photo_id in photo_ids for photo in followed_photos)

@patch("routes.photo.classify_image", return_value="mocked-nature")
@patch("routes.photo.describe_image", return_value="mocked-description")
def test_get_photo_of_day(mock_describe, mock_classify, client, feed_auth_headers, followed_photos):
    """Test that the photo with most likes is returned as photo_of_day"""
    response = client.get("/feed/", headers=feed_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "photo_of_day" in data
    assert data["photo_of_day"] is not None

    # Should be the photo with a like
    most_liked_photo = followed_photos[1]
    assert data["photo_of_day"]["photo_id"] == most_liked_photo.photo_id
