from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic
from sqlalchemy.orm import Session

from backend.dependencies.tables import get_db, User
from backend.routers import team, user

app = FastAPI()
security = HTTPBasic()
origins = ["http://localhost:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(team.router)
app.include_router(user.router)

@app.get("/debug/")
def get_debug_info(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users
