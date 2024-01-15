from pydantic import BaseModel


class TeamToInsert(BaseModel):
    name: str
    description: str = None


class UserToInsert(BaseModel):
    username: str
    password: str
