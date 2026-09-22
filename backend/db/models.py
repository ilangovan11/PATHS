from datetime import datetime, timezone

from sqlalchemy import Column, Integer, Float, String, Text

from db.database import Base


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class DecisionLog(Base):
    __tablename__ = "decision_logs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(String, default=utc_now_iso)  # ISO-8601 UTC

    attendance = Column(Integer)
    internal_marks = Column(Integer)
    assignments = Column(Integer)
    study_hours = Column(Float)
    backlog_count = Column(Integer)
    stress_level = Column(Integer)

    prediction = Column(String)
    action = Column(String)
    confidence = Column(Float)
    reason = Column(String)
    triggered_by = Column(String)

    # PATHS 2.0 additions (added by migration on existing databases)
    model_version = Column(String, nullable=True)
    decision_trace = Column(Text, nullable=True)  # JSON list of trace steps


class User(Base):
    __tablename__ = "users"

    email = Column(String, primary_key=True, index=True)
    password_hash = Column(String)
    role = Column(String, default="viewer")
    created_at = Column(String, default=utc_now_iso)