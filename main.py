from fastapi import FastAPI, HTTPException, Depends, Form
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette import status

from tables import Team, SessionLocal, User

app = FastAPI()
security = HTTPBasic()
# app.mount("/static", StaticFiles(directory="static"), name="static")
origins = ["http://localhost:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def authenticate_user(credentials: HTTPBasicCredentials = Depends(security), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials.username, User.password == credentials.password).first()
    if user:
        return user
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")


class TeamToInsert(BaseModel):
    name: str
    description: str = None


class UserToInsert(BaseModel):
    username: str
    password: str


@app.get("/group/", dependencies=[Depends(authenticate_user)])
def get_groups():
    return {"message": "You are logged in!"}


@app.post("/register/")
def register_user(new_user: UserToInsert, db: Session = Depends(get_db)):
    if len(new_user.username) > 24 or len(new_user.password) > 24 or len(new_user.password) < 4:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="wrong username or password")

    user = User(username=new_user.username, password=new_user.password)
    if db.query(User).filter(User.username == user.username).first() is None:
        db.add(user)
        db.commit()
        db.refresh(user)
        return {"message": "User registered successfully"}
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")


@app.post("/team/")
def add_team(team: TeamToInsert, db: Session = Depends(get_db)):
    team = Team(name=team.name, description=team.description)
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


@app.get("/team/{team_id}")
def get_team(team_id: int, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if team:
        return team
    else:
        raise HTTPException(status_code=404, detail="Team has not found")


@app.get("/teams/")
def get_teams(db: Session = Depends(get_db)):
    teams = db.query(Team).all()
    teams.sort(key=lambda team: team.name)
    for team in teams:
        print(team.name, " ", team.description)
    return teams


@app.delete("/team/")
def delete_team(team_id: int, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    print(team.id, " ", team.name, " ", team.description)
    if team:
        db.delete(team)
        db.commit()
        return {"message": "team deleted"}
    else:
        raise HTTPException(status_code=404, detail="team not found")


@app.get("/debug/")
def get_debug_info(db: Session=Depends(get_db)):
    users = db.query(User).all()
    return users