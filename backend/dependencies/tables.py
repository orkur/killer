from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, Table

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/users"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey('users.id'))
    password = Column(String)
    members = relationship("User", secondary="team_members")

    team_members = Table(
        "team_members",
        Base.metadata,
        Column("user_id", Integer, ForeignKey("users.id")),
        Column("team_id", Integer, ForeignKey("teams.id")),
    )

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)
