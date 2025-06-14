from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    Float, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class NutritionPlan(Base):
    __tablename__ = "nutrition_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    trainer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    
    # Plan details
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Nutritional targets
    daily_calories = Column(Integer, nullable=True)
    protein_grams = Column(Float, nullable=True)
    carbs_grams = Column(Float, nullable=True)
    fat_grams = Column(Float, nullable=True)
    fiber_grams = Column(Float, nullable=True)
    
    # Meal structure (JSON)
    # Structure: {"meals": [{"name": "Breakfast", "time": "08:00", "foods": [...]}]}
    meal_plan = Column(JSON, nullable=True)
    
    # Guidelines and notes
    guidelines = Column(Text, nullable=True)
    restrictions = Column(Text, nullable=True)  # Allergies, dietary restrictions
    notes = Column(Text, nullable=True)
    
    # Status
    is_template = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    trainer = relationship("User", back_populates="nutrition_plans")
    client = relationship("Client", back_populates="nutrition_plans")
    
    def __repr__(self):
        return f"<NutritionPlan {self.name}>"


class Food(Base):
    __tablename__ = "foods"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Food details
    name = Column(String(200), nullable=False)
    brand = Column(String(100), nullable=True)
    category = Column(String(100), nullable=True)
    
    # Nutritional information (per 100g)
    calories_per_100g = Column(Float, nullable=True)
    protein_per_100g = Column(Float, nullable=True)
    carbs_per_100g = Column(Float, nullable=True)
    fat_per_100g = Column(Float, nullable=True)
    fiber_per_100g = Column(Float, nullable=True)
    sugar_per_100g = Column(Float, nullable=True)
    sodium_per_100g = Column(Float, nullable=True)
    
    # Additional info
    serving_size = Column(String(50), nullable=True)
    barcode = Column(String(50), nullable=True)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_public = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Food {self.name}>"


# Add relationships to existing models
from app.models.user import User
from app.models.client import Client

User.nutrition_plans = relationship("NutritionPlan", back_populates="trainer")
User.foods = relationship("Food", foreign_keys=[Food.created_by])
Client.nutrition_plans = relationship("NutritionPlan", back_populates="client")
