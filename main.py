from datetime import timedelta, datetime
from jose import JWTError, jwt
from fastapi import FastAPI, HTTPException, Depends, Form
from fastapi.security import HTTPBasic, HTTPBasicCredentials, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette import status

from tables import Team, SessionLocal, User
from passlib.context import CryptContext

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
SECRET_KEY = "STRENG GEHEIM"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
password_hasher = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_jwt_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password, hashed_password):
    print(password_hasher.verify(plain_password, hashed_password))
    return password_hasher.verify(plain_password, hashed_password)

class TeamToInsert(BaseModel):
    name: str
    description: str = None


class UserToInsert(BaseModel):
    username: str
    password: str


@app.post("/login/")
def login(form: dict, db: Session = Depends(get_db)):
    username = form.get("username")
    password = form.get("password")
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Invalid credentials", headers={"WWW-Authenticate": "Bearer"})
    user_data = {"sub": user.id, "username": user.username}
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_jwt_token(data=user_data, expires_delta=access_token_expires)

    return {"access_token": access_token, "token_type": "bearer", "message": "User login successfully"}


@app.post("/register/")
def register_user(new_user: UserToInsert, db: Session = Depends(get_db)):
    if len(new_user.username) > 24 or len(new_user.password) > 24 or len(new_user.password) < 4:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="wrong username or password")

    user = User(username=new_user.username, password=new_user.password)
    if db.query(User).filter(User.username == user.username).first() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")

    user.password = password_hasher.hash(new_user.password)
    db.add(user)
    db.commit()
    db.refresh(user)
    user_data = {"sub": user.id, "username": user.username}
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_jwt_token(data=user_data, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer", "message": "User registered successfully"}


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
    # for team in teams:
    #     print(team.name, " ", team.description)
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
def get_debug_info(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users
