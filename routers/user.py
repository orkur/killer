from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from dependencies.tables import get_db, User
from models.models import UserToInsert
from routers.hasher import verify_password, ACCESS_TOKEN_EXPIRE_MINUTES, create_jwt_token, password_hasher

router = APIRouter()
@router.post("/login/")
def login_user(form: dict, db: Session = Depends(get_db)):
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
    user_data = {"sub": user.id, "username": user.username}
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_jwt_token(data=user_data, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer", "message": "User registered successfully"}
