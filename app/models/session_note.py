from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class SessionNote(Base):
    __tablename__ = "session_notes"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    trainer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)

    note_date = Column(Date, nullable=False)
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    is_private = Column(Boolean, default=False)  # private = only trainer sees it

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    client = relationship("Client", back_populates="session_notes")
    trainer = relationship("User")

    def __repr__(self):
        return f"<SessionNote {self.id} for client {self.client_id} on {self.note_date}>"
