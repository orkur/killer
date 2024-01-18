import copy
from random import random, shuffle

from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette import status

from backend.dependencies.tables import Team, get_db, User, Game, KillRequest
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

    next_player_id = players[(players.index(user_id) + 1) % len(players)]
    next_player = get_player_data(next_player_id, db)
    print(next_player)
    return next_player.username


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
    game = db.query(Game).filter(Game.team_id == team_id).first()
    if game is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="game not found")
    print(game.players)
    data = copy.deepcopy(game.players)
    data.remove(user_id)
    game.players = data
    print(game.players)
    db.commit()
    return {"message": "user has been killed successfully"}


@router.get('/test/')
def get_game(team_id: int, db: Session = Depends(get_db)):
    return db.query(Game).filter(Game.team_id == team_id).first()


@router.post('/team/killRequest/')
def kill_attempt(team_id: int, user_id: int, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.team_id == team_id)
    if game is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"game not found")
    players = game.players
    next_player_id = players[(players.index(user_id) + 1) % len(players)]
    request = KillRequest(team_id=team_id, player=next_player_id)
    db.add(request)
    db.commit()
    return {"message": "kill request has been sent"}


@router.get('/team/check/')
def check_kill_request(team_id: int, user_id: int, db: Session = Depends(get_db)):
    request = db.query(KillRequest).filter(KillRequest.team_id == team_id, KillRequest.user_id == user_id).first()
    if (request):
        return True
    return False
