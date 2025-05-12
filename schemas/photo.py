from pydantic import BaseModel , ConfigDict
from typing import Optional


class PhotoUploadResponse(BaseModel):
    photo_id: int
    filename: str

class PhotoListItem(BaseModel):
    photo_id: int
    owner_id: int
    tags: Optional[str]
    description: Optional[str]
    average_rating: int  
    likes: int           


    model_config = ConfigDict(from_attributes=True)

