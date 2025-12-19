from fastapi import APIRouter
from pydantic import BaseModel
from engine.decision import coordinate
from api.health import router as health_router

router = APIRouter()
router.include_router(health_router)

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
