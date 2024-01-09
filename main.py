
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from tables import Zespol, SessionLocal




app = FastAPI()

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

class ZespolDoWpisania(BaseModel):
    nazwa : str
    opis: str = None

@app.post("/zespol/")
def dodaj_zespol(zespol : ZespolDoWpisania, db: Session = Depends(get_db)):
    zespol = Zespol(nazwa=zespol.nazwa, opis=zespol.opis)
    db.add(zespol)
    db.commit()
    db.refresh(zespol)
    return zespol

@app.get("/zespol/{zespol_id}")
def pobierz_zespol(zespol_id: int, db: Session = Depends(get_db)):
    zespol = db.query(Zespol).filter(Zespol.id == zespol_id).first()
    if zespol:
        return zespol
    else:
        raise HTTPException(status_code=404, detail="Zespół nie został znaleziony")

@app.get("/zespoly/")
def pobierz_zespoly(db: Session = Depends(get_db)):
    zespoly = db.query(Zespol).all()
    # for zespol in zespoly:
    #     print(zespol.id , " " , zespol.nazwa , " " , zespol.opis)
    return zespoly

@app.post("/foo/")
def Witaj():
    return "Witaj Świecie!"
