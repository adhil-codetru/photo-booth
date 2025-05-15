from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, attributes
from typing import List
from dependencies import get_db
from auth import get_current_user
from models import Photo, User
import json
from schemas.comment import Comment, CommentCreate, CommentUpdate, CommentList

router = APIRouter(
    prefix="/comments",
    tags=["Comments"]
)

@router.get("/{photo_id}", response_model=CommentList)
def get_comments(photo_id: int, db: Session = Depends(get_db) , current_user : User = Depends(get_current_user)):
    photo = db.query(Photo).filter(Photo.photo_id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return {"comments": photo.comments or []}

@router.post("/{photo_id}", response_model=CommentList)
def add_comment(photo_id: int, comment: CommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    photo = db.query(Photo).filter(Photo.photo_id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    new_comment = {"username": current_user.username, "comment": comment.comment}

    
    if photo.comments is None:
        photo.comments = []
    
    photo.comments.append(new_comment)
    attributes.flag_modified(photo, "comments")
    
    db.commit()
    db.refresh(photo)
    return {"comments": photo.comments}

# @router.put("/{photo_id}/{index}", response_model=CommentList)
# def update_comment(photo_id: int, index: int, new_comment: CommentUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     photo = db.query(Photo).filter(Photo.photo_id == photo_id).first()
#     if not photo:
#         raise HTTPException(status_code=404, detail="Photo not found")
    
#     if not photo.comments or index >= len(photo.comments):
#         raise HTTPException(status_code=404, detail="Comment not found")
    
#     if photo.comments[index]["username"] != current_user.username:
#         raise HTTPException(status_code=403, detail="Not authorized to edit this comment")
    
#     updated_comments = photo.comments.copy()
#     updated_comments[index] = {
#         "username": photo.comments[index]["username"],
#         "comment": new_comment.new_comment

#     }
    
#     photo.comments = updated_comments
#     attributes.flag_modified(photo, "comments")
    
#     # Optional fallback: direct SQL update
#     from sqlalchemy import text
#     comment_json = json.dumps(updated_comments)
#     db.execute(
#         text("UPDATE photos SET comments = :comments WHERE photo_id = :photo_id"),
#         {"comments": comment_json, "photo_id": photo_id}
#     )
#     db.commit()
#     db.refresh(photo)
#     return {"comments": photo.comments}

@router.put("/{photo_id}/{index}", response_model=CommentList)
def update_comment(
    photo_id: int,
    index: int,
    new_comment: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    photo = db.query(Photo).filter(Photo.photo_id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    if not photo.comments or not isinstance(photo.comments, list):
        raise HTTPException(status_code=404, detail="No comments found")

    # Find all comments by current user
    user_comments = [
        (i, c) for i, c in enumerate(photo.comments)
        if c.get("username") == current_user.username
    ]

    if index >= len(user_comments):
        raise HTTPException(status_code=404, detail="Your comment at that index does not exist")

    # Get global index of the user’s comment to update
    global_index = user_comments[index][0]

    # Update the specific comment
    updated_comments = photo.comments.copy()
    updated_comments[global_index]["comment"] = new_comment.new_comment

    photo.comments = updated_comments
    attributes.flag_modified(photo, "comments")

    # Optional: ensure DB JSONB updates properly
    from sqlalchemy import text
    comment_json = json.dumps(updated_comments)
    db.execute(
        text("UPDATE photos SET comments = :comments WHERE photo_id = :photo_id"),
        {"comments": comment_json, "photo_id": photo_id}
    )

    db.commit()
    db.refresh(photo)
    return {"comments": photo.comments}

   
@router.delete("/{photo_id}/{index}", response_model=CommentList)
def delete_comment(photo_id: int, index: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    photo = db.query(Photo).filter(Photo.photo_id == photo_id).first()
    if not photo or not photo.comments or index >= len(photo.comments):
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if photo.comments[index]["username"] != current_user.username:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
    
    photo.comments.pop(index)
    attributes.flag_modified(photo, "comments")
    
    db.commit()
    db.refresh(photo)
    return {"comments": photo.comments}