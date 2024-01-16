from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from backend.dependencies.tables import Team, get_db, User
from backend.models.models import TeamToInsert, JoinToInsert

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
    if team:
        return team
    else:
        raise HTTPException(status_code=404, detail="Team has not found")


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


@router.delete("/team/")
def delete_team(team_id: int, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    print(team.id, " ", team.name, " ", team.description)
    if team:
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
        raise HTTPException(status_code=status.HTTP_418_IM_A_TEAPOT, detail="something unexpected had happeneds. "
                                                                            "Please refresh your page")
    if user not in team.members:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="user has not yet joined this team.")
    team.members.remove(user)
    db.commit()
    return
