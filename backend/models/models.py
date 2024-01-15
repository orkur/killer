from pydantic import BaseModel


class TeamToInsert(BaseModel):
    name: str
    description: str = None
    creator: int
    password: str = None


class UserToInsert(BaseModel):
    username: str
    password: str


class JoinToInsert(BaseModel):
    team_id: int
    user_id: int
    password: str = ""
