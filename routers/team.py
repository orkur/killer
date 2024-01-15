from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.orm import Session

from dependencies.tables import Team, get_db
from models.models import TeamToInsert

router = APIRouter()
@router.post("/team/")
def add_team(team: TeamToInsert, db: Session = Depends(get_db)):
    team = Team(name=team.name, description=team.description)
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


@router.get("/teams/")
def get_teams(db: Session = Depends(get_db)):
    teams = db.query(Team).all()
    teams.sort(key=lambda team: team.name)
    # for team in teams:
    #     print(team.name, " ", team.description)
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

