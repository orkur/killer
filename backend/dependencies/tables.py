from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, ForeignKey, Table

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import ARRAY

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/users"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

Base = declarative_base()

team_members = Table(
    "team_members",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("team_id", Integer, ForeignKey("teams.id")),
)


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
    closed = Column(Boolean, default=False)
    started = Column(Boolean, default=False)

    @hybrid_property
    def public(self):
        return {"id": self.id, "name": self.name, "description": self.description}


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    teams = relationship("Team", secondary="team_members", viewonly=True)


class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    players = Column(ARRAY(Integer), index=True)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)
