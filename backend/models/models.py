from pydantic import BaseModel


class TeamToInsert(BaseModel):
    name: str
    description: str = None
    creator: int


class UserToInsert(BaseModel):
    username: str
    password: str
