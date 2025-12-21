from sqlalchemy import Column, Integer, Float, String
from db.database import Base

class DecisionLog(Base):
    __tablename__ = "decision_logs"

    id = Column(Integer, primary_key=True, index=True)
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
