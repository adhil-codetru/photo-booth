from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_db
from auth import get_current_user
from models import Like, Photo, User
from schemas.like import LikeResponse, LikeCountResponse

router = APIRouter(
    prefix="/likes",
    tags=["Likes"]
)

@router.post("/{photo_id}", response_model=LikeResponse)
def like_photo(photo_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    photo = db.query(Photo).filter(Photo.photo_id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    existing_like = db.query(Like).filter(
        Like.user_id == current_user.user_id,
        Like.photo_id == photo_id
    ).first()

    if existing_like:
        raise HTTPException(status_code=400, detail="You have already liked this photo")

    new_like = Like(user_id=current_user.user_id, photo_id=photo_id)
    db.add(new_like)
    db.commit()

    return {"message": "Photo liked successfully"}


@router.delete("/{photo_id}", response_model=LikeResponse)
def unlike_photo(photo_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    like = db.query(Like).filter(
        Like.user_id == current_user.user_id,
        Like.photo_id == photo_id
    ).first()

    if not like:
        raise HTTPException(status_code=404, detail="Like not found")

    db.delete(like)
    db.commit()
    return {"message": "Photo unliked successfully"}


@router.get("/{photo_id}", response_model=LikeCountResponse)
def get_photo_likes(photo_id: int, db: Session = Depends(get_db) , current_user : User = Depends(get_current_user)):
    count = db.query(Like).filter(Like.photo_id == photo_id).count()
    return {"photo_id": photo_id, "like_count": count}
