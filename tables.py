from sqlalchemy import create_engine, Column, Integer, String, Text

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/users"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


Base.metadata.create_all(bind=engine)


class Zespol(Base):
    __tablename__ = "zespoly"

    id = Column(Integer, primary_key=True, index=True)
    nazwa = Column(String, index=True)
    opis = Column(Text)
