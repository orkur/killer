import copy
from random import random, shuffle

from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette import status

from backend.dependencies.tables import Team, get_db, User, Game, KillRequest
from backend.models.models import TeamToInsert, JoinToInsert
from backend.routers.user import get_members_from_team, get_player_data, check_registered_user

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
    if user_id not in players:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player does not exist")
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


@router.get("/team/number/{team_id}")
def get_number_of_players(team_id: int, db: Session = Depends(get_db)) -> int:
    game = db.query(Game).filter(Game.team_id == team_id).first()
    return len(game.players)

@router.post('/team/delete/')
def delete_player(info: dict, db: Session = Depends(get_db)):
    team_id, user_id = int(info["team_id"]), int(info["user_id"])

    if not check_registered_user(user_id, info["password"], db):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="wrong password")

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
def kill_attempt(info: dict, db: Session = Depends(get_db)):
    team_id, user_id = info['team_id'], info['user_id']
    game: Game = db.query(Game).filter(Game.team_id == team_id).first()
    print(game.id, game.team_id, game.players)
    if game is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"game not found")
    players = game.players
    next_player_id = players[(players.index(user_id) + 1) % len(players)]
    request = KillRequest(team_id=team_id, user_id=next_player_id)
    if (db.query(KillRequest)
            .filter(KillRequest.team_id == team_id, KillRequest.user_id == next_player_id)
            .first() is not None):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"your victim hasn't answered yet.")

    db.add(request)
    db.commit()
    return {"message": "kill request has been sent"}


@router.get('/team/check/')
def check_kill_request(team_id: int, user_id: int, db: Session = Depends(get_db)):
    request = db.query(KillRequest).filter(KillRequest.team_id == team_id, KillRequest.user_id == user_id).first()
    if request:
        return True
    return False


@router.post('/team/disagree/')
def abort_kill_request(info: dict, db: Session = Depends(get_db)):
    team_id, user_id = int(info["team_id"]), int(info["user_id"])
    request = db.query(KillRequest).filter(KillRequest.team_id == team_id, KillRequest.user_id == user_id).first()
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    db.delete(request)
    db.commit()
    return {"message": "request has been sent"}


@router.get('/team/alive/')
def check_if_alive(team_id: int, user_id: int, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.team_id == team_id).first()
    print(user_id, game.players)
    if user_id in game.players:
        return True
    return False
