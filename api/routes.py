from fastapi import APIRouter
from pydantic import BaseModel
from engine.decision import coordinate

router = APIRouter()

class StudentInput(BaseModel):
    attendance: int
    internal_marks: int
    assignments: int
    study_hours: float
    backlog_count: int
    stress_level: int

@router.post("/coordinate")
def run_coordinate(data: StudentInput):
    raw_input = [
        data.attendance,
        data.internal_marks,
        data.assignments,
        data.study_hours,
        data.backlog_count,
        data.stress_level
    ]
    return coordinate(raw_input)
