from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class GoalMilestone(Base):
    __tablename__ = "goal_milestones"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    trainer_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Goal definition
    title = Column(String(200), nullable=False)          # e.g. "Lose 10kg"
    goal_type = Column(String(50), nullable=False)        # weight_loss | muscle_gain | etc.
    metric = Column(String(100), nullable=False)          # e.g. "weight" | "body_fat" | "custom"
    unit = Column(String(20), nullable=True)              # kg | % | reps | km

    # Progress values
    start_value = Column(Float, nullable=False)
    target_value = Column(Float, nullable=False)
    current_value = Column(Float, nullable=True)          # updated manually or from body metrics

    # Timeline
    start_date = Column(Date, nullable=False)
    target_date = Column(Date, nullable=True)

    # Status
    is_completed = Column(Boolean, default=False)
    completed_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    client = relationship("Client", back_populates="goal_milestones")
    trainer = relationship("User")

    def __repr__(self):
        return f"<GoalMilestone {self.title} for client {self.client_id}>"
