from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List

from models import User , Photo
from schemas.user import UserCreate, UserOut , UserUpdate
from dependencies import get_db
from auth import get_current_user
from utils import hash_password
import os
router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.post("/", response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    if user.role != 'User' and user.role != 'Photographer':
        raise HTTPException(status_code=400,detail="Invalid User role")
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_pw = hash_password(user.password)
    new_user = User(
        username=user.username,
        password=hashed_pw,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/", response_model=List[UserOut])
def get_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(User).offset(skip).limit(limit).all()

@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    updated_user: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update fields only if non-empty and not None
    if updated_user.username:
        user.username = updated_user.username.strip()

    if updated_user.password:
        user.password = hash_password(updated_user.password.strip())

    if updated_user.role in {"User", "Photographer"}:
        user.role = updated_user.role

    db.commit()
    db.refresh(user)
    return user




@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this user")

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch all photos owned by the user
    user_photos = db.query(Photo).filter(Photo.owner_id == user_id).all()

    # Delete associated photo files from disk
    for photo in user_photos:
        if photo.file_path and os.path.exists(photo.file_path):
            try:
                os.remove(photo.file_path)
            except Exception as e:
                print(f"Error deleting file {photo.file_path}: {e}")

    # Now delete the user (which cascades to photos, likes, etc.)
    db.delete(user)
    db.commit()
    return None

