from sqlalchemy import Column, Integer, Float, String, Date, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class BodyMetric(Base):
    __tablename__ = "body_metrics"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)

    # Date of measurement
    measured_at = Column(Date, nullable=False)

    # Core metrics
    weight = Column(Float, nullable=True)           # kg
    body_fat_percentage = Column(Float, nullable=True)  # %
    muscle_mass = Column(Float, nullable=True)       # kg

    # Body measurements (cm)
    waist = Column(Float, nullable=True)
    chest = Column(Float, nullable=True)
    hips = Column(Float, nullable=True)
    arms = Column(Float, nullable=True)
    thighs = Column(Float, nullable=True)

    # Optional trainer note for this entry
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    client = relationship("Client", back_populates="body_metrics")

    def __repr__(self):
        return f"<BodyMetric client={self.client_id} date={self.measured_at}>"
