try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Database
    database_url: str = ""
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "fitness_coach_user"
    db_password: str = "password"
    db_name: str = "fitness_coach_db"
    
    # Security
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001"
    
    @property 
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    # Environment
    environment: str = "development"
    
    # Email
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    @property
    def database_url_computed(self) -> str:
        # Check if DATABASE_URL is set directly (priority)
        if self.database_url:
            return self.database_url
        
        # Default to SQLite for development
        return "sqlite:///./fitness_coach.db"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
