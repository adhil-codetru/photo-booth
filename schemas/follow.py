from pydantic import BaseModel,ConfigDict


class FollowResponse(BaseModel):
    detail: str


class UnfollowResponse(BaseModel):
    detail: str


class FollowedUser(BaseModel):
    user_id: int
    username: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class FollowList(BaseModel):
    users: list[FollowedUser]
