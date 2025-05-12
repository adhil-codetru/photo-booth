from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from dependencies import get_db
from auth import get_current_user
from models import User, Follower
from schemas.follow import FollowResponse , UnfollowResponse , FollowList , FollowedUser
router = APIRouter(
    prefix="/follow",
    tags=["Follow"]
)

@router.post("/{user_id}", response_model=FollowResponse)
def follow_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself.")

    target_user = db.query(User).filter(User.user_id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Enforce role-based follow rules
    if current_user.role == "User" and target_user.role != "Photographer":
        raise HTTPException(status_code=403, detail="Users can only follow photographers.")

    if current_user.role == "Photographer" and target_user.role == "User":
        raise HTTPException(status_code=403, detail="Photographers cannot follow users.")

    existing_follow = db.query(Follower).filter_by(user_id=user_id, follower_id=current_user.user_id).first()
    if existing_follow:
        raise HTTPException(status_code=400, detail="Already following this user.")

    follow = Follower(user_id=user_id, follower_id=current_user.user_id)
    db.add(follow)
    db.commit()
    return {"detail": f"You are now following {target_user.username}."}



@router.delete("/{user_id}" , response_model=UnfollowResponse)
def unfollow_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    follow = db.query(Follower).filter_by(user_id=user_id, follower_id=current_user.user_id).first()
    if not follow:
        raise HTTPException(status_code=404, detail="You are not following this user.")

    db.delete(follow)
    db.commit()
    return {"detail": "Successfully unfollowed."}

@router.get("/following", response_model=FollowList)
def get_following(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    following = (
        db.query(User)
        .join(Follower, Follower.user_id == User.user_id)
        .filter(Follower.follower_id == current_user.user_id)
        .all()
    )
    return {"users": following}


@router.get("/followers", response_model=FollowList)
def get_followers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    followers = (
        db.query(User)
        .join(Follower, Follower.follower_id == User.user_id)
        .filter(Follower.user_id == current_user.user_id)
        .all()
    )
    return {"users": followers}

