"""POST /coordinate — the core decision endpoint.

Backend validation is authoritative (Pydantic Field bounds). The engine
result (prediction/action/confidence/reason + trace + model version) is
persisted to SQLite with a timestamp and the model version used.
"""

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth.security import admin_only
from db.database import get_db
from db.models import DecisionLog
from engine.decision import coordinate
from core.logging import get_logger

router = APIRouter()
logger = get_logger()


class StudentInput(BaseModel):
    # Ranges documented in core/validation.py; enforced at the API boundary.
    attendance: int = Field(..., ge=0, le=100)
    internal_marks: int = Field(..., ge=0, le=100)
    assignments: int = Field(..., ge=0, le=100)
    study_hours: float = Field(..., ge=0.0, le=16.0)
    backlog_count: int = Field(..., ge=0, le=20)
    stress_level: int = Field(..., ge=1, le=10)


@router.post("/coordinate")
def run_coordinate(
    data: StudentInput,
    user=Depends(admin_only),
    db: Session = Depends(get_db),
):
    if data.attendance < 0 or data.stress_level < 1 or data.stress_level > 10:
        raise HTTPException(status_code=422, detail="Invalid feature values")

    raw = [
        data.attendance,
        data.internal_marks,
        data.assignments,
        data.study_hours,
        data.backlog_count,
        data.stress_level,
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
        triggered_by=user["sub"],
        model_version=result["model_version"],
        decision_trace=json.dumps(result["trace"]),
    )
    db.add(log)
    db.commit()

    logger.info(
        "Decision recorded: %s (%s) by %s using %s",
        result["action"],
        result["prediction"],
        user["sub"],
        result["model_version"],
    )

    return result