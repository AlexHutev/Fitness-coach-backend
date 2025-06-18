from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt

from app.core.config import settings
from app.models import ProgramAssignment, Client, Program, User
from app.schemas.client_schemas import (
    ClientLoginRequest, ClientTokenResponse, ClientCreateCredentials
)


class ClientAuthService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        return self.pwd_context.hash(password)
    
    def create_client_access_token(self, assignment_id: int, client_id: int) -> str:
        """Create JWT token for client access"""
        data = {
            "sub": str(client_id),
            "assignment_id": assignment_id,
            "type": "client_access",
            "exp": datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes or 30)
        }
        return jwt.encode(data, settings.secret_key or "default-secret", algorithm=settings.algorithm or "HS256")
    
    def verify_client_token(self, token: str) -> Optional[dict]:
        """Verify and decode client JWT token"""
        try:
            payload = jwt.decode(token, settings.secret_key or "default-secret", algorithms=[settings.algorithm or "HS256"])
            client_id: str = payload.get("sub")
            assignment_id: int = payload.get("assignment_id")
            token_type: str = payload.get("type")
            
            if client_id is None or assignment_id is None or token_type != "client_access":
                return None
                
            return {
                "client_id": int(client_id),
                "assignment_id": assignment_id,
                "token_type": token_type
            }
        except JWTError:
            return None
    
    def authenticate_client(self, db: Session, email: str, password: str) -> Optional[ProgramAssignment]:
        """Authenticate client and return their program assignment"""
        from app.models.program_assignment import AssignmentStatus
        
        assignment = (
            db.query(ProgramAssignment)
            .filter(ProgramAssignment.client_access_email == email)
            .filter(ProgramAssignment.status == AssignmentStatus.ACTIVE)
            .first()
        )
        
        if not assignment or not assignment.client_hashed_password:
            return None
            
        if not self.verify_password(password, assignment.client_hashed_password):
            return None
            
        return assignment
    
    def login_client(self, db: Session, login_request: ClientLoginRequest) -> Optional[ClientTokenResponse]:
        """Handle client login and return token response"""
        assignment = self.authenticate_client(db, login_request.email, login_request.password)
        
        if not assignment:
            return None
        
        # Get program details
        program = db.query(Program).filter(Program.id == assignment.program_id).first()
        
        if not program:
            return None
        
        # Create access token
        access_token = self.create_client_access_token(assignment.id, assignment.client_id)
        
        return ClientTokenResponse(
            access_token=access_token,
            token_type="bearer",
            client_id=assignment.client_id,
            assignment_id=assignment.id,
            program_name=program.name
        )
    
    def create_client_credentials(
        self, 
        db: Session, 
        assignment_id: int, 
        email: str, 
        password: str
    ) -> bool:
        """Create login credentials for a client's program assignment"""
        assignment = db.query(ProgramAssignment).filter(ProgramAssignment.id == assignment_id).first()
        
        if not assignment:
            return False
        
        # Check if email is already in use
        existing = (
            db.query(ProgramAssignment)
            .filter(ProgramAssignment.client_access_email == email)
            .filter(ProgramAssignment.id != assignment_id)
            .first()
        )
        
        if existing:
            return False
        
        # Set client credentials
        assignment.client_access_email = email
        assignment.client_hashed_password = self.get_password_hash(password)
        
        db.commit()
        db.refresh(assignment)
        
        return True
    
    def get_client_assignment_from_token(self, db: Session, token: str) -> Optional[ProgramAssignment]:
        """Get client's program assignment from JWT token"""
        from app.models.program_assignment import AssignmentStatus
        
        token_data = self.verify_client_token(token)
        
        if not token_data:
            return None
        
        assignment = (
            db.query(ProgramAssignment)
            .filter(ProgramAssignment.id == token_data["assignment_id"])
            .filter(ProgramAssignment.client_id == token_data["client_id"])
            .filter(ProgramAssignment.status == AssignmentStatus.ACTIVE)
            .first()
        )
        
        return assignment
    
    def update_client_password(
        self, 
        db: Session, 
        assignment_id: int, 
        new_password: str
    ) -> bool:
        """Update client's password"""
        assignment = db.query(ProgramAssignment).filter(ProgramAssignment.id == assignment_id).first()
        
        if not assignment:
            return False
        
        assignment.client_hashed_password = self.get_password_hash(new_password)
        db.commit()
        
        return True


# Global instance
client_auth_service = ClientAuthService()