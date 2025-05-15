import pytest
from models import User
from utils import hash_password
from auth import create_access_token

@pytest.fixture(scope="function")
def seed_data(db):
    # Create a test user
    user = User(username="testuser", password=hash_password("testpass"), role="User")
    db.add(user)
    db.commit()
    db.refresh(user)  # Refresh to get the ID
    
    # Return user for tests that need it
    yield user

@pytest.fixture
def auth_headers(seed_data):
    # Create access token for the test user
    access_token = create_access_token(data={"sub": seed_data.username})
    return {"Authorization": f"Bearer {access_token}"}

def test_create_user(client):
    response = client.post("/users/", json={
        "username": "anotheruser",
        "password": "newpass",
        "role": "Photographer"
    })
    assert response.status_code == 200
    assert response.json()["username"] == "anotheruser"

def test_get_users(client, seed_data, auth_headers):
    response = client.get("/users/" , headers=auth_headers)
    assert response.status_code == 200
    assert any(user["username"] == "testuser" for user in response.json())

def test_get_user_by_id(client, seed_data , auth_headers):
    # Use the user created in seed_data
    user_id = seed_data.user_id
    response = client.get(f"/users/{user_id}" , headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

def test_update_user(client, seed_data, auth_headers):
    user_id = seed_data.user_id
    response = client.put(
        f"/users/{user_id}",
        json={
            "username": "updateduser",
            "password": "newpass",
            "role": "Photographer"
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["username"] == "updateduser"

def test_delete_user(client, auth_headers):
    # Create a user to delete
    response = client.post("/users/", json={
        "username": "tobedeleted",
        "password": "deletepass",
        "role": "User"
    })
    assert response.status_code == 200
    user_id = response.json()["user_id"]
    
    # Log in as the user we're about to delete
    login_response = client.post(
        "/token",
        data={"username": "tobedeleted", "password": "deletepass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    delete_headers = {"Authorization": f"Bearer {token}"}
    
    # Delete the user
    delete_resp = client.delete(f"/users/{user_id}", headers=delete_headers)
    assert delete_resp.status_code == 204
    
    # Verify user is deleted
    get_resp = client.get(f"/users/{user_id}")
    assert get_resp.status_code == 401