"""Read-only analytics backed by real decision-log rows.

Accessible to any authenticated user (viewer = read-only analyst role).
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth.security import get_current_user
from db.database import get_db
from db.models import DecisionLog

router = APIRouter(prefix="/analytics")


@router.get("/summary")
def decision_summary(user=Depends(get_current_user), db: Session = Depends(get_db)):
    advance = db.query(DecisionLog).filter(DecisionLog.action == "ADVANCE").count()
    hold = db.query(DecisionLog).filter(DecisionLog.action == "HOLD").count()
    retreat = db.query(DecisionLog).filter(DecisionLog.action == "RETREAT").count()

    return {
        "total_decisions": advance + hold + retreat,
        "advance": advance,
        "hold": hold,
        "retreat": retreat,
    }


@router.get("/confidence")
def confidence_stats(user=Depends(get_current_user), db: Session = Depends(get_db)):
    avg_conf = db.query(func.avg(DecisionLog.confidence)).scalar()
    max_conf = db.query(func.max(DecisionLog.confidence)).scalar()
    min_conf = db.query(func.min(DecisionLog.confidence)).scalar()
    count = db.query(DecisionLog).count()

    return {
        "average_confidence": round(float(avg_conf or 0), 4),
        "max_confidence": round(float(max_conf or 0), 4),
        "min_confidence": round(float(min_conf or 0), 4),
        "count": count,
    }


@router.get("/stress-impact")
def stress_impact(user=Depends(get_current_user), db: Session = Depends(get_db)):
    data = (
        db.query(
            DecisionLog.stress_level,
            DecisionLog.action,
            func.count().label("count"),
        )
        .group_by(DecisionLog.stress_level, DecisionLog.action)
        .all()
    )

    result = {}
    for stress, action, count in data:
        result.setdefault(int(stress), {})[action] = count
    return result


@router.get("/recent")
def recent_decisions(
    limit: int = 10,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    limit = max(1, min(int(limit), 50))
    rows = (
        db.query(DecisionLog)
        .order_by(DecisionLog.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "created_at": r.created_at,
            "action": r.action,
            "prediction": r.prediction,
            "confidence": r.confidence,
            "reason": r.reason,
            "model_version": r.model_version,
            "triggered_by": r.triggered_by,
        }
        for r in rows
    ]