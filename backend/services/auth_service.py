from sqlalchemy.orm import Session
from models import User, PresenceStatus
from fastapi import HTTPException, status
import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from typing import Optional

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

class AuthService:
    def __init__(self, db: Session):
        self.db = db
    
    def register_user(self, username: str, email: str, password: str) -> dict:
        """
        Register a new user.
        
        Checks for existing email/username, hashes password, creates user record.
        Returns user data (excluding password hash).
        """
        # Check if email already exists
        existing_email = self.db.query(User).filter(User.email == email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if username already exists
        existing_username = self.db.query(User).filter(User.username == username).first()
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=password_hash.decode('utf-8'),
            presence_status=PresenceStatus.OFFLINE
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    
    def authenticate_user(self, email: str, password: str) -> Optional[dict]:
        """
        Authenticate a user by email and password.
        
        Returns user data if credentials are valid, None otherwise.
        """
        # Find user by email
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return None
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return None
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    
    def create_token(self, user_id: int, username: str, email: str) -> str:
        """Create a JWT token for authenticated user"""
        expiration = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": str(user_id),
            "username": username,
            "email": email,
            "exp": expiration
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """Find a user by ID - used for JWT validation"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "presence_status": user.presence_status.value if user.presence_status else "offline",
            "last_seen": user.last_seen.isoformat() if user.last_seen else None
        }
    
    def update_last_seen(self, user_id: int) -> None:
        """Update user's last_seen timestamp - called on WebSocket activity"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.last_seen = datetime.now()
            self.db.commit()
    
    # Fixed: Renamed parameter from 'status' to 'presence_status' to avoid conflict
    def update_presence(self, user_id: int, presence_status: str) -> None:
        """Update user's presence status"""
        try:
            presence_enum = PresenceStatus(presence_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid presence status: {presence_status}"
            )
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.presence_status = presence_enum
            user.last_seen = datetime.now()
            self.db.commit()