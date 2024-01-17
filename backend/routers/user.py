from datetime import timedelta
from enum import member

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from backend.dependencies.tables import get_db, User, Team
from backend.models.models import UserToInsert
from backend.routers.hasher import verify_password, ACCESS_TOKEN_EXPIRE_MINUTES, create_jwt_token, password_hasher

router = APIRouter()


def make_user_data(user_id: int, name: str) -> dict:
    return {"id": user_id, "username": name}


@router.post("/login/")
def login_user(form: dict, db: Session = Depends(get_db)):
    username = form.get("username")
    password = form.get("password")
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Invalid credentials", headers={"WWW-Authenticate": "Bearer"})
    user_data = make_user_data(user.id, user.username)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_jwt_token(data=user_data, expires_delta=access_token_expires)

    return {"access_token": access_token, "token_type": "bearer", "message": "User login successfully"}


@router.post("/register/")
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
    user_data = make_user_data(user.id, user.username)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_jwt_token(data=user_data, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer", "message": "User registered successfully"}

@router.get("/players/")
def get_members_from_team(team_id: int, db: Session = Depends(get_db)):
    members = db.query(User.id, User.username).filter(User.teams.any(id=team_id)).all()
    members = [{"id": member.id, "name": member.username} for member in members]
    return members


def get_player_data(user_id: int, db: Session = Depends(get_db)):
    return db.query(User.id, User.username).filter(User.id == user_id).first()