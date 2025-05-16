#photo.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status , Query , BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from dependencies import get_db
from auth import get_current_user
from models import User , Photo , SharePhoto , Follower
from schemas.photo import PhotoUploadResponse, PhotoListItem
from services.ai_utils import classify_image, describe_image
from settings import UPLOAD_DIR
from datetime import datetime
from services.share_utils import clean_expired_shares
router = APIRouter(
    prefix="/photos",
    tags=["Photos"]
)

# @router.post('/share/{photo_id}/{user_id}')
# def share_photo(
#     photo_id: int,
#     user_id: int,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     photo = db.query(Photo).filter(Photo.photo_id == photo_id).first()
    
#     if not photo:
#         raise HTTPException(status_code=404, detail="Photo not found")
    
#     if photo.owner_id != current_user.user_id:
#         raise HTTPException(status_code=401, detail="A user can only share their own photos")
    
#     if current_user.role != 'Photographer':
#         raise HTTPException(status_code=401, detail="Only Photographers can share photos")

#     shared_photo = SharePhoto(photo_id=photo_id, user_id=user_id)

#     db.add(shared_photo)  
#     db.commit()          
#     return {"message": "Photo shared successfully", "shared_with_user_id": user_id}

from datetime import datetime, timedelta

@router.post('/share/{photo_id}/{user_id}')
def share_photo(
    photo_id: int,
    user_id: int,
    hours: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    photo = db.query(Photo).filter(Photo.photo_id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    if photo.owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    if current_user.role != 'Photographer':
        raise HTTPException(status_code=403, detail="Only photographers can share photos")

    expiration_time = datetime.utcnow() + timedelta(hours=hours)

    share = SharePhoto(
        photo_id=photo_id,
        user_id=user_id,
        expires_at=expiration_time
    )
    db.add(share)
    db.commit()

    return {
        "message": "Photo shared successfully",
        "shared_with_user_id": user_id,
        "expires_at": expiration_time.isoformat()
    }

@router.delete('/share/{photo_id}/{user_id}')
def remove_share(
    photo_id : int,
    user_id: int,
    db : Session = Depends(get_db),
    current_user : User = Depends(get_current_user)
):
    photo = db.query(Photo).filter(Photo.photo_id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404 , detail="Photo not found")
    if photo.owner_id != current_user.user_id:
        raise HTTPException(status_code=403 , detail="You do not have accesss")
    shared = db.query(SharePhoto).filter(SharePhoto.photo_id == photo_id , SharePhoto.user_id == user_id).first()
    if not shared:
        raise HTTPException(status_code=400 , detail="No shared link present")
    db.delete(shared)
    db.commit()
    return {"message" : "Photo sharing revoked succesfully"}

# @router.post("/upload", status_code=status.HTTP_201_CREATED, response_model=PhotoUploadResponse)
# def upload_photo(
#     file: UploadFile = File(...),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     if current_user.role != 'Photographer':
#         raise HTTPException(status_code=403, detail="Only Photographers can upload Photos")

#     file_ext = os.path.splitext(file.filename)[1].lower()
#     if file_ext not in [".jpg", ".jpeg", ".png", ".gif"]:
#         raise HTTPException(status_code=400, detail="Invalid image format")

#     # Create photo DB record with placeholders to get photo_id
#     new_photo = Photo(
#         owner_id=current_user.user_id,
#         comments=[],
#         tags="",  
#         description="",  
#         file_path=""  #
#     )
#     db.add(new_photo)
#     db.flush()  

#     # Construct unique file name and path
#     file_name = f"{new_photo.photo_id}{file_ext}"
#     file_path = os.path.join(UPLOAD_DIR, file_name)

#     # Save file to disk
#     with open(file_path, "wb") as f:
#         f.write(file.file.read())

#     # AI tagging and description
#     try:
#         predicted_tag = classify_image(file_path)
#         auto_description = describe_image(file_path)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"AI service failed: {str(e)}")

#     # Update photo record with real data
#     new_photo.file_path = file_path
#     new_photo.tags = predicted_tag["category"]
#     new_photo.description = auto_description["description"]



#     db.commit()
#     db.refresh(new_photo)

#     return {"photo_id": new_photo.photo_id, "filename": file_name}
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

    # Create placeholder photo entry
    new_photo = Photo(
        owner_id=current_user.user_id,
        comments=[],
        tags="",
        description="",
        file_path=""
    )
    db.add(new_photo)
    db.flush()  # Assigns photo_id

    # Construct filename and save path
    file_name = f"{new_photo.photo_id}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    try:
        # Save image to disk
        with open(file_path, "wb") as f:
            f.write(file.file.read())

        # Run AI models
        predicted_tag = classify_image(file_path)
        auto_description = describe_image(file_path)

        # Update photo with AI results
        new_photo.file_path = file_path
        new_photo.tags = predicted_tag["category"]
        new_photo.description = auto_description["description"]

        db.commit()
        db.refresh(new_photo)

        return {"photo_id": new_photo.photo_id, "filename": file_name}

    except Exception as e:
        # Rollback DB changes
        db.rollback()

        # Clean up any saved file
        if os.path.exists(file_path):
            os.remove(file_path)

        # Clean up photo record (only needed if flushed ID already added a record)
        db.query(Photo).filter(Photo.photo_id == new_photo.photo_id).delete()
        db.commit()

        raise HTTPException(status_code=500, detail=f"Upload failed due to AI service error: {str(e)}")


@router.get("/{photo_id}/view")
def view_photo(
    photo_id: int,
    background_tasks : BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    background_tasks.add_task(clean_expired_shares,db)
    photo = db.query(Photo).filter(Photo.photo_id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    is_owner = photo.owner_id == current_user.user_id

    is_shared = db.query(SharePhoto).filter(
        SharePhoto.photo_id == photo_id,
        SharePhoto.user_id == current_user.user_id,
        SharePhoto.expires_at > datetime.utcnow()  # Check expiry
    ).first()

    is_following = db.query(Follower).filter(
        Follower.follower_id == current_user.user_id,
        Follower.user_id == photo.owner_id
    ).first()

    if not is_owner and not is_shared and not is_following:
        raise HTTPException(status_code=403, detail="Access denied")

    if not os.path.exists(photo.file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(photo.file_path)


@router.get("/", response_model=List[PhotoListItem])
def list_photos(skip: int = 0, limit: int = 10, db: Session = Depends(get_db) , current_user : User = Depends(get_current_user)):
    if current_user.role != 'Photographer':
        raise HTTPException(status_code=403 , detail="Only Photographers can view this route")
    photos = db.query(Photo).filter(Photo.owner_id == current_user.user_id).offset(skip).limit(limit).all()
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

    filepath = photo.file_path
    

    if os.path.exists(filepath):
        os.remove(filepath)

    db.delete(photo)
    db.commit()
    return
