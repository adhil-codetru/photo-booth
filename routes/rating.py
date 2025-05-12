from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from dependencies import get_db
from auth import get_current_user
from models import Photo, User, Rating
from schemas.rating import RatingResponse, RatingUpdateResponse, MessageResponse

router = APIRouter(
    prefix="/ratings",
    tags=["Ratings"]
)

@router.get("/photo/{photo_id}", response_model=RatingResponse)
def get_photo_rating(photo_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    photo = db.query(Photo).filter(Photo.photo_id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    avg_rating = db.query(func.avg(Rating.photo_rating)).filter(Rating.photo_id == photo_id).scalar()
    user_rating = db.query(Rating.photo_rating).filter(
        Rating.photo_id == photo_id,
        Rating.user_id == current_user.user_id
    ).scalar()

    return RatingResponse(
        average_rating=round(avg_rating or 0, 2),
        user_rating=user_rating
    )

@router.post("/photo/{photo_id}", response_model=RatingUpdateResponse)
def rate_photo(photo_id: int, rating: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not (1 <= rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    photo = db.query(Photo).filter(Photo.photo_id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    existing_rating = db.query(Rating).filter(
        Rating.user_id == current_user.user_id,
        Rating.photo_id == photo_id
    ).first()

    if existing_rating:
        existing_rating.photo_rating = rating
    else:
        new_rating = Rating(user_id=current_user.user_id, photo_id=photo_id, photo_rating=rating)
        db.add(new_rating)

    db.commit()

    avg_rating = db.query(func.avg(Rating.photo_rating)).filter(Rating.photo_id == photo_id).scalar()
    photo.average_rating = round(avg_rating or 0)
    db.commit()

    return RatingUpdateResponse(
        message="Photo rating updated",
        average_rating=photo.average_rating
    )

@router.delete("/photo/{photo_id}", response_model=RatingUpdateResponse)
def delete_photo_rating(photo_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rating = db.query(Rating).filter(Rating.user_id == current_user.user_id, Rating.photo_id == photo_id).first()
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    db.delete(rating)
    db.commit()

    avg_rating = db.query(func.avg(Rating.photo_rating)).filter(Rating.photo_id == photo_id).scalar()
    photo = db.query(Photo).filter(Photo.photo_id == photo_id).first()
    if photo:
        photo.average_rating = round(avg_rating or 0)
        db.commit()

    return RatingUpdateResponse(
        message="Photo rating deleted",
        average_rating=photo.average_rating
    )
@router.get("/photographer/{photographer_id}", response_model=RatingResponse)
def get_photographer_rating(photographer_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    photographer = db.query(User).filter(User.user_id == photographer_id, User.role == 'Photographer').first()
    if not photographer:
        raise HTTPException(status_code=404, detail="Photographer not found")

    avg_rating = db.query(func.avg(Rating.photographer_rating)).filter(
        Rating.photographer_id == photographer_id
    ).scalar()

    user_rating = db.query(Rating.photographer_rating).filter(
        Rating.photographer_id == photographer_id,
        Rating.user_id == current_user.user_id
    ).scalar()

    return RatingResponse(
        average_rating=round(avg_rating or 0, 2),
        user_rating=user_rating
    )


@router.post("/photographer/{photographer_id}", response_model=RatingUpdateResponse)
def rate_photographer(photographer_id: int, rating: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not (1 <= rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    photographer = db.query(User).filter(User.user_id == photographer_id, User.role == 'Photographer').first()
    if not photographer:
        raise HTTPException(status_code=404, detail="Photographer not found")

    existing_rating = db.query(Rating).filter(
        Rating.user_id == current_user.user_id,
        Rating.photographer_id == photographer_id
    ).first()

    if existing_rating:
        existing_rating.photographer_rating = rating
    else:
        new_rating = Rating(user_id=current_user.user_id, photographer_id=photographer_id, photographer_rating=rating)
        db.add(new_rating)

    db.commit()

    avg_rating = db.query(func.avg(Rating.photographer_rating)).filter(
        Rating.photographer_id == photographer_id
    ).scalar()

    photographer.rating = round(avg_rating or 0)
    db.commit()

    return RatingUpdateResponse(
        message="Photographer rating updated",
        average_rating=photographer.rating
    )


@router.delete("/photographer/{photographer_id}", response_model=RatingUpdateResponse)
def delete_photographer_rating(photographer_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rating = db.query(Rating).filter(Rating.user_id == current_user.user_id, Rating.photographer_id == photographer_id).first()
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    db.delete(rating)
    db.commit()

    avg_rating = db.query(func.avg(Rating.photographer_rating)).filter(Rating.photographer_id == photographer_id).scalar()
    photographer = db.query(User).filter(User.user_id == photographer_id).first()
    if photographer:
        photographer.rating = round(avg_rating or 0)
        db.commit()

    return RatingUpdateResponse(
        message="Photographer rating deleted",
        average_rating=photographer.rating
    )
