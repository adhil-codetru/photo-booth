from pydantic import BaseModel , ConfigDict
from typing import List, Optional

class FeedPhoto(BaseModel):
    photo_id: int
    owner_id: int
    file_path: str
    tags: Optional[str]
    description: Optional[str]
    average_rating: float
    like_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)
class FeedResponse(BaseModel):
    feed_photos: List[FeedPhoto]
    photo_of_day: Optional[FeedPhoto]
