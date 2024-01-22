from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from backend.dependencies.tables import Team, get_db, User, Game, KillRequest
from backend.gameLogic.graph import create_graph
from backend.models.models import TeamToInsert, JoinToInsert, AdminAndTeam

router = APIRouter()


@router.post("/team/")
def add_team(team: TeamToInsert, db: Session = Depends(get_db)):
    team = Team(name=team.name, description=team.description, created_by=team.creator, password=team.password)
    if db.query(Team).filter(Team.name == team.name).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="team already exists")
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


@router.get("/team/{team_id}")
def get_team(team_id: int, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    print(team, " prz")
    if team:
        return team
    else:
        raise HTTPException(status_code=404, detail="Team has not found")


@router.get("/teamName/")
def get_team_names(team_id: int, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    return team.name


def get_teams(db: Session = Depends(get_db)):
    teams = db.query(Team).all()
    teams = [team.public for team in teams]
    return teams


def list_all_id_of_joined_teams(user_id: int, db: Session = Depends(get_db)):
    teams = db.query(Team.id, Team.name).filter(Team.members.any(id=user_id)).all()
    return teams


@router.get("/relation/list")
def list_of_relation_with_teams(user_id: int, db: Session = Depends(get_db)):
    teams = sorted(get_teams(db), key=lambda team: team['name'])
    occupying_teams = sorted(list_all_id_of_joined_teams(user_id, db), key=lambda team: team[1])
    occupying_teams = [team[0] for team in occupying_teams]
    i = 0

    def f(team, occupying_teams):
        nonlocal i
        if occupying_teams and i < len(occupying_teams) and team['id'] == occupying_teams[i]:
            i += 1
            return {'l': team, 'r': True}
        else:
            return {'l': team, 'r': False}

    teams = [f(team, occupying_teams) for team in teams]
    return teams


@router.delete("/team/{team_id}")
def delete_team(team_id: int, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()

    print(team.id, " ", team.name, " ", team.description)
    if team:
        game = db.query(Game).filter(Game.team_id == team_id).delete()
        kill = db.query(KillRequest).filter(KillRequest.team_id == team_id).delete()
        db.delete(team)
        db.commit()
        return {"message": "team deleted"}
    else:
        raise HTTPException(status_code=404, detail="team not found")


# INFO inefficient, many useless calls to database
@router.get("/exist/")
def check_exist(team_id: int, user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    team = db.query(Team).filter(Team.id == team_id).first()
    if user and team and (user in team.members):
        return True
    return False


@router.post("/relation/join/")
def join_team(relation: JoinToInsert, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == relation.user_id).first()
    team = db.query(Team).filter(Team.id == relation.team_id).first()
    print(relation.password)
    if team.password != relation.password:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="wrong password")
    if not user or not team:
        raise HTTPException(status_code=status.HTTP_418_IM_A_TEAPOT, detail="something unexpected had happeneds. "
                                                                            "Please refresh your page")
    if user in team.members:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="user belongs to this team.")
    team.members.append(user)
    db.commit()
    return


@router.post("/relation/exit/")
def exit_team(relation: JoinToInsert, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == relation.user_id).first()
    team = db.query(Team).filter(Team.id == relation.team_id).first()

    if not user or not team:
        raise HTTPException(status_code=status.HTTP_418_IM_A_TEAPOT, detail="something unexpected had happens. "
                                                                            "Please refresh your page")
    if user not in team.members:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="user has not yet joined this team.")
    team.members.remove(user)
    db.commit()
    return {"message": "user exited successfully"}


@router.get("/admin/")
def is_admin(team_id: int, user_id: int, db: Session = Depends(get_db)):
    if db.query(Team).filter(Team.id == team_id, Team.created_by == user_id).first():
        return True
    else:
        return False

@router.get("/gameStarted/")
def is_game_started(team_id: int, db: Session = Depends(get_db)):
    start_game = db.query(Team.started).filter(Team.id == team_id).first()
    if start_game is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="game not found")
    return start_game[0]
@router.post("/access/")
def change_accessibility_of_team(team_id: int, user_id: int, close: bool, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if team.created_by != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="user isn't an admin of this team.")
    if team.started:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="user cannot change access when game started.")
    team.closed = close
    return {"message": "accessibility of team has been updated."}


@router.post("/startGame/")
def start_game(admin: AdminAndTeam, db: Session = Depends(get_db)):
    team_id = admin.team_id
    user_id = admin.user_id
    print(team_id, user_id)
    team = db.query(Team).filter(Team.id == team_id).first()
    if team.created_by != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="user isn't an admin of this team.")
    team.closed = True
    team.started = True
    db.commit()
    create_graph(team_id, db)

    return {"message": "game created"}

@router.get("/isClosedGame/{team_id}")
def is_closed_game(team_id: int, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    return team.closed
