from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy.orm import Session
import jwt
import os
from ..dependencies import get_db
from services import AuthService

# JWT Configuration (needed for get_current_user)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"

router = APIRouter(prefix="/auth", tags=["authentication"])

# Request/Response Models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class MessageResponse(BaseModel):
    message: str
    user_id: Optional[int] = None



@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    Accepts username, email, and password. Hashes the password before storing.
    Returns a success message upon completion.
    """
    auth_service = AuthService(db)
    user = auth_service.register_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password
    )
    
    return MessageResponse(
        message="User registered successfully",
        user_id=user["id"]
    )

@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate a user and return a JWT token.
    
    Accepts email and password, verifies credentials against stored hash.
    Returns a JWT token for subsequent authenticated requests.
    """
    auth_service = AuthService(db)
    
    # Authenticate user
    user = auth_service.authenticate_user(
        email=credentials.email,
        password=credentials.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create JWT token
    token = auth_service.create_token(
        user_id=user["id"],
        username=user["username"],
        email=user["email"]
    )
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"]
        )
    )

# Helper function to get current user from token (used by WebSocket and other routes)
def get_current_user(token: str, db: Session):
    """
    Validate JWT token and return current user.
    This is used by WebSocket connections and as a fallback.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        
        auth_service = AuthService(db)
        return auth_service.get_user_by_id(user_id)
    except jwt.PyJWTError:
        return None