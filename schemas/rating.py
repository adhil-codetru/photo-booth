from pydantic import BaseModel, Field
from typing import Optional


class RatingResponse(BaseModel):
    average_rating: float = Field(..., description="The average rating (rounded to 2 decimals)")
    user_rating: Optional[int] = Field(None, description="The current user's rating, if available")


class RatingUpdateResponse(BaseModel):
    message: str
    average_rating: float


class MessageResponse(BaseModel):
    message: str
