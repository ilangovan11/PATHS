from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from engine.decision import coordinate
from auth.security import admin_only
from db.database import SessionLocal
from db.models import DecisionLog

router = APIRouter()

class StudentInput(BaseModel):
    attendance: int
    internal_marks: int
    assignments: int
    study_hours: float
    backlog_count: int
    stress_level: int

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/coordinate")
def run_coordinate(
    data: StudentInput,
    user=Depends(admin_only),
    db: Session = Depends(get_db)
):
    raw = [
        data.attendance,
        data.internal_marks,
        data.assignments,
        data.study_hours,
        data.backlog_count,
        data.stress_level
    ]

    result = coordinate(raw)

    log = DecisionLog(
        attendance=data.attendance,
        internal_marks=data.internal_marks,
        assignments=data.assignments,
        study_hours=data.study_hours,
        backlog_count=data.backlog_count,
        stress_level=data.stress_level,
        prediction=result["prediction"],
        action=result["action"],
        confidence=result["confidence"],
        reason=result["reason"],
        triggered_by=user["sub"]
    )

    db.add(log)
    db.commit()

    return result