from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from models import Message, Channel
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime

class MessageService:
    def __init__(self, db: Session):
        self.db = db
    
    def save_message(self, channel_id: int, user_id: int, username: str, content: str) -> dict:
        """
        Save a new message to the database.
        
        Called by WebSocket handler when messages arrive.
        Raises ValueError for validation errors (WebSocket-safe)
        """
        # Verify channel exists
        channel = self.db.query(Channel).filter(Channel.id == channel_id).first()
        if not channel:
            raise ValueError("Channel not found")
        
        # Validate message length
        if not content or len(content.strip()) == 0:
            raise ValueError("Message cannot be empty")
        
        if len(content) > 2000:  # TODO: Get max length from server settings
            raise ValueError("Message exceeds maximum length of 2000 characters")
        
        # Create message
        message = Message(
            content=content.strip(),
            user_id=user_id,
            username=username,  # Denormalized for history
            channel_id=channel_id
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        # TODO: After commit, trigger AI sidecar for embedding
        
        return {
            "id": message.id,
            "content": message.content,
            "user_id": message.user_id,
            "username": message.username,
            "channel_id": message.channel_id,
            "timestamp": message.timestamp.isoformat() if message.timestamp else None
        }
    
    def get_channel_messages(
        self, 
        channel_id: int, 
        limit: int = 50, 
        before: Optional[datetime] = None
    ) -> List[dict]:
        """Get message history for a channel"""
        query = self.db.query(Message)\
            .filter(Message.channel_id == channel_id)
        
        if before:
            query = query.filter(Message.timestamp < before)
        
        messages = query.order_by(desc(Message.timestamp))\
            .limit(limit)\
            .all()
        
        # Return in chronological order (oldest first)
        messages.reverse()
        
        return [{
            "id": m.id,
            "content": m.content,
            "user_id": m.user_id,
            "username": m.username,
            "channel_id": m.channel_id,
            "timestamp": m.timestamp.isoformat() if m.timestamp else None,
            "is_edited": m.is_edited,
            "edited_at": m.edited_at.isoformat() if m.edited_at else None
        } for m in messages]
    
    def get_message_by_id(self, message_id: int) -> Optional[dict]:
        """Get a single message by ID"""
        message = self.db.query(Message).filter(Message.id == message_id).first()
        if not message:
            return None
        
        return {
            "id": message.id,
            "content": message.content,
            "user_id": message.user_id,
            "username": message.username,
            "channel_id": message.channel_id,
            "timestamp": message.timestamp.isoformat() if message.timestamp else None,
            "is_edited": message.is_edited,
            "edited_at": message.edited_at.isoformat() if message.edited_at else None
        }
    
    def edit_message(self, message_id: int, user_id: int, new_content: str) -> Optional[dict]:
        """
        Edit an existing message.
        
        Only the original author can edit their message.
        Note: This method uses HTTPException because it's called from HTTP routes.
        For WebSocket-called methods, use ValueError instead.
        """
        message = self.db.query(Message).filter(Message.id == message_id).first()
        if not message:
            return None
        
        # Check if user is the author
        if message.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot edit another user's message"
            )
        
        # Validate new content
        if not new_content or len(new_content.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )
        
        # Update message
        message.content = new_content.strip()
        message.is_edited = True
        message.edited_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(message)
        
        return {
            "id": message.id,
            "content": message.content,
            "user_id": message.user_id,
            "username": message.username,
            "channel_id": message.channel_id,
            "timestamp": message.timestamp.isoformat() if message.timestamp else None,
            "is_edited": message.is_edited,
            "edited_at": message.edited_at.isoformat() if message.edited_at else None
        }