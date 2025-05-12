from pydantic import BaseModel


class LikeResponse(BaseModel):
    message: str


class LikeCountResponse(BaseModel):
    photo_id: int
    like_count: int
