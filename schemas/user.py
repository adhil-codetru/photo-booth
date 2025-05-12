from pydantic import BaseModel , ConfigDict
from typing import Optional
class UserCreate(BaseModel):
    username: str
    password: str
    role: str  # e.g., "User" or "Photographer"

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None


class UserOut(BaseModel):
    user_id: int
    username: str
    role: str
    rating: int

    model_config = ConfigDict(from_attributes = True)



