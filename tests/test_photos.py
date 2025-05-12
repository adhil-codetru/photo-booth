import pytest
import os
import io
from PIL import Image
import numpy as np
from unittest.mock import patch, MagicMock
from fastapi import UploadFile
from models import Photo, User
from utils import hash_password
from auth import create_access_token
from database import Base, engine, SessionLocal
from settings import settings
from sqlalchemy.orm import Session

# Create test directory for uploads
TEST_UPLOAD_DIR = "test_uploaded_photos"
os.makedirs(TEST_UPLOAD_DIR, exist_ok=True)

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

@pytest.fixture(autouse=True)
def mock_dependencies():
    """Mock all external dependencies"""
    with patch("routes.photo.UPLOAD_DIR", TEST_UPLOAD_DIR), \
         patch("settings.UPLOAD_DIR", TEST_UPLOAD_DIR):
        yield

def create_test_image():
    """Create a simple test image in memory"""
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr

@pytest.fixture(scope="function")
def test_user(db: Session):
    # Create test users
    user = User(
        username="testuser",
        password=hash_password("testpass"),
        role="User"
    )
    photographer = User(
        username="testphotographer",
        password=hash_password("testpass"),
        role="Photographer"
    )
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
def test_photo(db: Session, test_user):
    """Create a test photo with file"""
    # First create the photo record
    photo = Photo(
        owner_id=test_user["photographer"].user_id,
        file_path=os.path.join(TEST_UPLOAD_DIR, "1.jpg"),
        tags="nature",
        description="A beautiful landscape"
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    
    # Create a proper test image file
    img = create_test_image()
    with open(photo.file_path, "wb") as f:
        f.write(img.getvalue())
    
    yield photo
    
    # Cleanup
    if os.path.exists(photo.file_path):
        os.remove(photo.file_path)

@patch("routes.photo.classify_image", return_value="nature")
@patch("routes.photo.describe_image", return_value="A beautiful landscape")
def test_upload_photo_as_photographer(mock_describe, mock_classify, client, auth_headers, test_user, db):
    """Test photo upload by photographer"""
    # Verify test directory exists and is writable
    assert os.path.exists(TEST_UPLOAD_DIR)
    assert os.access(TEST_UPLOAD_DIR, os.W_OK)
    
    # Create proper test image
    test_image = create_test_image()
    
    response = client.post(
        "/photos/upload",
        files={"file": ("test.jpg", test_image, "image/jpeg")},
        headers=auth_headers["photographer"]
    )
    
    # Debug output if test fails
    if response.status_code != 201:
        print("ERROR RESPONSE:", response.json())
    
    assert response.status_code == 201
    data = response.json()
    assert "photo_id" in data
    assert "filename" in data
    
    # Verify file was created
    photo_id = data["photo_id"]
    expected_path = os.path.join(TEST_UPLOAD_DIR, f"{photo_id}.jpg")
    assert os.path.exists(expected_path)
    
    # Verify AI services were called
    mock_classify.assert_called_once()
    mock_describe.assert_called_once()
    
    # Cleanup
    if os.path.exists(expected_path):
        os.remove(expected_path)

def test_view_photo(client, test_photo):
    """Test viewing a photo"""
    response = client.get(f"/photos/{test_photo.photo_id}/view")
    assert response.status_code == 200
    # Verify it returns an image
    assert response.headers["content-type"] == "image/jpeg"

def test_list_photos(client, test_photo):
    """Test listing photos"""
    response = client.get("/photos/")
    assert response.status_code == 200
    photos = response.json()
    assert any(p["photo_id"] == test_photo.photo_id for p in photos)

def test_delete_own_photo(client, test_photo, auth_headers, db):
    """Test photographer can delete their own photo"""
    # First verify photo exists
    assert os.path.exists(test_photo.file_path)
    
    response = client.delete(
        f"/photos/{test_photo.photo_id}",
        headers=auth_headers["photographer"]
    )
    assert response.status_code == 204
    
    # Verify deletion from database
    deleted_photo = db.query(Photo).filter(Photo.photo_id == test_photo.photo_id).first()
    assert deleted_photo is None
    
    # Verify file was deleted
    assert not os.path.exists(test_photo.file_path)

def test_delete_other_users_photo(client, test_photo, auth_headers):
    """Test regular user cannot delete photographer's photo"""
    response = client.delete(
        f"/photos/{test_photo.photo_id}",
        headers=auth_headers["user"]
    )
    assert response.status_code == 404
    assert "Photo not found or not authorized" in response.json()["detail"]