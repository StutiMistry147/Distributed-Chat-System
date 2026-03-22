from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from ..dependencies import get_token_user, get_db
from services import MessageService, ChannelService

router = APIRouter(prefix="/messages", tags=["messages"])

# Request/Response Models
class MessageResponse(BaseModel):
    id: int
    content: str
    user_id: Optional[int]
    username: str
    channel_id: int
    timestamp: datetime

@router.get("/{channel_id}", response_model=List[MessageResponse])
async def get_channel_messages(
    channel_id: int,
    limit: int = Query(50, ge=1, le=100, description="Number of messages to return"),
    before: Optional[datetime] = Query(None, description="Get messages before this timestamp"),
    user: dict = Depends(get_token_user),
    db: Session = Depends(get_db)
):
    """
    Get message history for a channel.
    
    Accepts a channel ID and returns the last N messages in chronological order.
    Includes sender info and timestamp. Used to load initial chat history.
    User must be a member of the parent server.
    """
    # Verify user has access to channel
    channel_service = ChannelService(db)
    if not channel_service.verify_channel_access(channel_id, user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this channel's server"
        )
    
    # Get messages
    message_service = MessageService(db)
    messages = message_service.get_channel_messages(
        channel_id=channel_id,
        limit=limit,
        before=before
    )
    
    return [MessageResponse(
        id=m["id"],
        content=m["content"],
        user_id=m["user_id"],
        username=m["username"],
        channel_id=m["channel_id"],
        timestamp=m["timestamp"]
    ) for m in messages]

# Note: The add_message helper function is removed - use MessageService directly