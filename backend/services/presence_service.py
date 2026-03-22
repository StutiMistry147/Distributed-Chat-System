from datetime import datetime

from sqlalchemy.orm import Session
from models import User, Membership, PresenceStatus
from fastapi import HTTPException, status
from typing import List, Dict, Optional

class PresenceService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_server_presences(self, server_id: int) -> List[Dict]:
        """
        Get presence status of all members in a server.
        
        Returns list of users with their current presence status.
        """
        memberships = self.db.query(Membership)\
            .filter(Membership.server_id == server_id)\
            .all()
        
        user_ids = [m.user_id for m in memberships if m.user_id]
        
        if not user_ids:
            return []
        
        users = self.db.query(User)\
            .filter(User.id.in_(user_ids))\
            .all()
        
        return [{
            "user_id": user.id,
            "username": user.username,
            "presence": user.presence_status.value if user.presence_status else "offline",
            "last_seen": user.last_seen.isoformat() if user.last_seen else None
        } for user in users]
    
    def update_presence(self, user_id: int, presence_status: str) -> Dict:
        """
        Update a single user's presence status.
        
        Returns the updated user data.
        """
        # Validate presence status
        try:
            presence_enum = PresenceStatus(presence_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid presence status: {presence_status}"
            )
        
        # Update user directly (no need to delegate to AuthService)
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.presence_status = presence_enum
        user.last_seen = datetime.now()
        self.db.commit()
        
        return {
            "user_id": user.id,
            "username": user.username,
            "presence": user.presence_status.value if user.presence_status else "offline",
            "last_seen": user.last_seen.isoformat() if user.last_seen else None
        }
    
    def get_online_count(self, server_id: int) -> int:
        """Get count of currently online users in a server"""
        memberships = self.db.query(Membership)\
            .filter(Membership.server_id == server_id)\
            .all()
        
        user_ids = [m.user_id for m in memberships if m.user_id]
        
        if not user_ids:
            return 0
        
        online_count = self.db.query(User)\
            .filter(
                User.id.in_(user_ids),
                User.presence_status == PresenceStatus.ONLINE
            )\
            .count()
        
        return online_count
    
    def get_user_presence(self, user_id: int) -> Optional[Dict]:
        """Get presence status for a single user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return None
        
        return {
            "user_id": user.id,
            "username": user.username,
            "presence": user.presence_status.value if user.presence_status else "offline",
            "last_seen": user.last_seen.isoformat() if user.last_seen else None
        }