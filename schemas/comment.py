from pydantic import BaseModel
from typing import List

class Comment(BaseModel):
    username: str
    comment: str

class CommentCreate(BaseModel):
    comment: str

class CommentUpdate(BaseModel):
    new_comment: str

class CommentList(BaseModel):
    comments: List[Comment]
