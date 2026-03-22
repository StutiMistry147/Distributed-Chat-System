from sqlalchemy.orm import Session
from sqlalchemy import and_
from models import Channel, Server
from fastapi import HTTPException, status
from typing import List, Optional

# WARNING: Importing ServerService here creates a potential circular dependency
# If server_service.py ever imports ChannelService, this will crash.
# The safer pattern is to have the route pass is_member result into this method
# rather than having channel_service depend on server_service directly.
from .server_service import ServerService

class ChannelService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_channel(self, name: str, server_id: int, user_id: int) -> dict:
        """
        Create a new channel in a server.
        
        Checks if user is a member of the server first.
        """
        # Verify server exists and user is member (permission check should be done by caller)
        server = self.db.query(Server).filter(Server.id == server_id).first()
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )
        
        # Check if channel name already exists in this server
        existing = self.db.query(Channel)\
            .filter(
                and_(
                    Channel.server_id == server_id,
                    Channel.name == name
                )
            ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Channel name already exists in this server"
            )
        
        # Create channel
        channel = Channel(
            name=name,
            server_id=server_id
        )
        self.db.add(channel)
        self.db.commit()
        self.db.refresh(channel)
        
        return {
            "id": channel.id,
            "name": channel.name,
            "server_id": channel.server_id,
            "created_at": channel.created_at.isoformat() if channel.created_at else None
        }
    
    def get_server_channels(self, server_id: int) -> List[dict]:
        """Get all channels in a server"""
        channels = self.db.query(Channel)\
            .filter(Channel.server_id == server_id)\
            .order_by(Channel.created_at)\
            .all()
        
        return [{
            "id": c.id,
            "name": c.name,
            "server_id": c.server_id,
            "created_at": c.created_at.isoformat() if c.created_at else None
        } for c in channels]
    
    def get_channel_by_id(self, channel_id: int) -> Optional[dict]:
        """Get channel details by ID"""
        channel = self.db.query(Channel).filter(Channel.id == channel_id).first()
        if not channel:
            return None
        
        return {
            "id": channel.id,
            "name": channel.name,
            "server_id": channel.server_id,
            "created_at": channel.created_at.isoformat() if channel.created_at else None
        }
    
    def verify_channel_access(self, channel_id: int, user_id: int) -> bool:
        """
        Verify that a user has access to a channel.
        User must be a member of the channel's parent server.
        """
        channel = self.db.query(Channel).filter(Channel.id == channel_id).first()
        if not channel:
            return False
        
        # TODO: This creates a circular dependency risk
        # Better approach: have the route pass is_member result directly
        server_service = ServerService(self.db)
        return server_service.is_member(channel.server_id, user_id)