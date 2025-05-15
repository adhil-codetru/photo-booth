import pytest
from models import User, Photo
from utils import hash_password
from auth import create_access_token
from sqlalchemy.orm import Session


@pytest.fixture
def comment_users(db: Session):
    user = User(username="comment_user", password=hash_password("pass"), role="User")
    other_user = User(username="other_user", password=hash_password("pass"), role="User")
    db.add_all([user, other_user])
    db.commit()
    db.refresh(user)
    db.refresh(other_user)
    return {"user": user, "other_user": other_user}


@pytest.fixture
def comment_auth_headers(comment_users):
    token = create_access_token(data={"sub": comment_users["user"].username})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def photo_with_comments(db: Session, comment_users):
    photo = Photo(
        owner_id=comment_users["user"].user_id,
        file_path="commentable.jpg",
        comments=[
            {"username": comment_users["user"].username, "comment": "Original comment"},
            {"username": comment_users["other_user"].username, "comment": "Other's comment"}
        ]
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo


def test_get_comments(client, photo_with_comments,comment_auth_headers):
    response = client.get(f"/comments/{photo_with_comments.photo_id}",
                          headers=comment_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "comments" in data
    assert len(data["comments"]) == 2


def test_add_comment(client, photo_with_comments, comment_auth_headers):
    response = client.post(
        f"/comments/{photo_with_comments.photo_id}",
        headers=comment_auth_headers,
        json={"comment": "New test comment"}
    )
    assert response.status_code == 200
    data = response.json()
    assert any(c["comment"] == "New test comment" for c in data["comments"])


def test_update_comment(client, photo_with_comments, comment_auth_headers):
    response = client.put(
        f"/comments/{photo_with_comments.photo_id}/0",
        headers=comment_auth_headers,
        json={"new_comment": "Updated comment"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["comments"][0]["comment"] == "Updated comment"


def test_update_comment_unauthorized(client, photo_with_comments, comment_auth_headers):
    # User tries to update someone else's comment
    response = client.put(
        f"/comments/{photo_with_comments.photo_id}/1",
        headers=comment_auth_headers,
        json={"new_comment": "Hacked"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Your comment at that index does not exist"


def test_delete_comment(client, photo_with_comments, comment_auth_headers):
    response = client.delete(
        f"/comments/{photo_with_comments.photo_id}/0",
        headers=comment_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert all(c["username"] != "comment_user" for c in data["comments"])


def test_delete_comment_unauthorized(client, photo_with_comments, comment_auth_headers):
    # User tries to delete someone else's comment
    response = client.delete(
        f"/comments/{photo_with_comments.photo_id}/1",
        headers=comment_auth_headers
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to delete this comment"
