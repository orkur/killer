from random import random, shuffle

from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette import status

from backend.dependencies.tables import Team, get_db, User, Game
from backend.models.models import TeamToInsert, JoinToInsert
from backend.routers.user import get_members_from_team, get_player_data

router = APIRouter()


@router.post("/team/makeGraph/")
def create_graph(team_id: int, db: Session = Depends(get_db)):
    members = get_members_from_team(team_id, db)
    members = [member['id'] for member in members]
    print(members)
    shuffle(members)
    print(members)
    game = Game(team_id=team_id, players=members)
    if db.query(Game).filter(Game.team_id == team_id).all():
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Game exists")
    db.add(game)
    db.commit()
    db.refresh(game)
    return


@router.get("/team/nextPlayer/")
def find_next_player(team_id: int, user_id: int, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.team_id == team_id).first()
    players = game.players
    print(players)
    print(players[(players.index(user_id) + 1) % len(players)])
    next_player_id = players[(players.index(user_id) + 1) % len(players)]
    next_player = get_player_data(next_player_id, db)
    print(next_player)
    return {"id": next_player.id, "name": next_player.username}


@router.get("/team/winner/")
def is_winner(team_id: int, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.team_id == team_id).first()
    print(game.players)
    if len(game.players) == 1:
        player = get_player_data(game.players[0], db)
        return {"id": player.id, "name": player.username}
    else:
        return {}

@router.post('/fooo/')
def delete_player(team_id: int, user_id: int, db: Session = Depends(get_db)):
    game = db.execute(select(Game).filter(Game.team_id == team_id)).scalar_one()
    print(game.players)
    game.players.remove(user_id)
    print(game.players)
    db.flush()
    db.commit()
    return