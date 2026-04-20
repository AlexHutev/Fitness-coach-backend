from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class PerformanceRecord(Base):
    __tablename__ = "performance_records"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    trainer_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # What exercise / lift
    exercise_name = Column(String(200), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=True)  # optional link

    # The performance value
    value = Column(Float, nullable=False)           # e.g. 100
    unit = Column(String(20), nullable=False)        # kg | lbs | reps | seconds | km
    record_type = Column(String(50), nullable=False) # e.g. "1RM" | "Max Reps" | "Best Time"

    # Context
    recorded_at = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)
    is_pr = Column(Integer, default=1)  # 1 = personal record flag

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    client = relationship("Client", back_populates="performance_records")
    trainer = relationship("User")
    exercise = relationship("Exercise", foreign_keys=[exercise_id])

    def __repr__(self):
        return f"<PerformanceRecord {self.exercise_name} {self.value}{self.unit}>"
