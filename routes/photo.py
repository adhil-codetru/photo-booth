#photo.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from models import Photo
from dependencies import get_db
from auth import get_current_user
from models import User
from schemas.photo import PhotoUploadResponse, PhotoListItem
from services.ai_utils import classify_image, describe_image
from settings import UPLOAD_DIR

router = APIRouter(
    prefix="/photos",
    tags=["Photos"]
)

@router.post("/upload", status_code=status.HTTP_201_CREATED, response_model=PhotoUploadResponse)
def upload_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != 'Photographer':
        raise HTTPException(status_code=403, detail="Only Photographers can upload Photos")

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".jpg", ".jpeg", ".png", ".gif"]:
        raise HTTPException(status_code=400, detail="Invalid image format")

    # Create photo DB record with placeholders to get photo_id
    new_photo = Photo(
        owner_id=current_user.user_id,
        comments=[],
        tags="",  # temporary
        description="",  # temporary
        file_path=""  # temporary to satisfy NOT NULL
    )
    db.add(new_photo)
    db.flush()  # Assigns photo_id without committing

    # Construct unique file name and path
    file_name = f"{new_photo.photo_id}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    # Save file to disk
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    # AI tagging and description
    try:
        predicted_tag = classify_image(file_path)
        auto_description = describe_image(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service failed: {str(e)}")

    # Update photo record with real data
    new_photo.file_path = file_path
    new_photo.tags = predicted_tag
    new_photo.description = auto_description

    db.commit()
    db.refresh(new_photo)

    return {"photo_id": new_photo.photo_id, "filename": file_name}


@router.get("/{photo_id}/view")
def view_photo(photo_id: int, db: Session = Depends(get_db)):
    photo = db.query(Photo).filter(Photo.photo_id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    filename = f"{photo_id}.jpg"
    filepath = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(filepath)

@router.get("/", response_model=List[PhotoListItem])
def list_photos(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    photos = db.query(Photo).offset(skip).limit(limit).all()
    photo_list = []
    for photo in photos:
        photo_dict = {
            "photo_id": photo.photo_id,
            "owner_id": photo.owner_id,
            "tags": photo.tags,
            "description": photo.description,
            "average_rating": photo.average_rating,
            "likes": len(photo.likes)
        }
        photo_list.append(photo_dict)

    return photo_list


@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_photo(photo_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    photo = db.query(Photo).filter(Photo.photo_id == photo_id, Photo.owner_id == current_user.user_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found or not authorized")

    filename = f"{photo_id}.jpg"
    filepath = os.path.join(UPLOAD_DIR, filename)

    if os.path.exists(filepath):
        os.remove(filepath)

    db.delete(photo)
    db.commit()
    return
