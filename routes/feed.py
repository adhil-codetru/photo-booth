from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, select
from models import User, Photo, Follower, Like
from dependencies import get_db
from auth import get_current_user
from schemas.feed import FeedResponse, FeedPhoto

router = APIRouter(
    prefix="/feed",
    tags=["Feed"]
)

@router.get("/", response_model=FeedResponse)
def get_user_feed(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get photographers the user is following
    followed_photographers_subq = (
        db.query(User.user_id)
        .join(Follower, Follower.user_id == User.user_id)
        .filter(
            Follower.follower_id == current_user.user_id,
            User.role == "Photographer"
        )
        .subquery()
    )

   
    followed_select = select(followed_photographers_subq)

    #  Get their photos
    feed_photos_query = (
        db.query(
            Photo.photo_id,
            Photo.owner_id,
            Photo.file_path,
            Photo.tags,
            Photo.description,
            Photo.average_rating,
            func.count(Like.photo_id).label("like_count")
        )
        .outerjoin(Like, Like.photo_id == Photo.photo_id)
        .filter(Photo.owner_id.in_(followed_select))
        .group_by(Photo.photo_id,Photo.file_path)
    )

    feed_photos = [
        FeedPhoto(
            photo_id=row.photo_id,
            owner_id=row.owner_id,
            file_path=row.file_path,
            tags=row.tags,
            description=row.description,
            average_rating=row.average_rating,
            like_count=row.like_count
        )
        for row in feed_photos_query.all()
    ]

    # Step 3: Get photo of the day
    photo_of_day_query = (
        db.query(
            Photo.photo_id,
            Photo.owner_id,
            Photo.file_path,
            Photo.tags,
            Photo.description,
            Photo.average_rating,
            func.count(Like.photo_id).label("like_count")
        )
        .join(Like, Like.photo_id == Photo.photo_id)
        .group_by(Photo.photo_id,Photo.file_path)
        .order_by(desc("like_count"), desc(Photo.photo_id))
        .limit(1)
        .first()
    )

    photo_of_day = None
    if photo_of_day_query:
        photo_of_day = FeedPhoto(
            photo_id=photo_of_day_query.photo_id,
            owner_id=photo_of_day_query.owner_id,
            file_path=photo_of_day_query.file_path,
            tags=photo_of_day_query.tags,
            description=photo_of_day_query.description,
            average_rating=photo_of_day_query.average_rating,
            like_count=photo_of_day_query.like_count
        )

    return {
        "feed_photos": feed_photos,
        "photo_of_day": photo_of_day
    }
