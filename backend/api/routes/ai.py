from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from ..dependencies import get_token_user, get_db
from services import AIService, ChannelService, ServerService
from services.ai_service import background_embed_message
from models import Message  # Moved to top level

router = APIRouter(prefix="/ai", tags=["ai"])

# Request/Response Models
class SearchQuery(BaseModel):
    query: str
    channel_id: Optional[int] = None
    top_k: int = 10

class SearchResult(BaseModel):
    id: int
    content: str
    username: str
    user_id: Optional[int]
    channel_id: int
    timestamp: Optional[str]
    score: float

class SummaryResponse(BaseModel):
    summary: str

@router.post("/search", response_model=List[SearchResult])
async def semantic_search(
    search_data: SearchQuery,
    user: dict = Depends(get_token_user),
    db: Session = Depends(get_db)
):
    """
    Search messages using natural language.
    
    Accepts a query string and returns semantically similar messages.
    Can optionally filter by channel_id.
    """
    ai_service = AIService(db)
    
    results = ai_service.search_similar(
        query=search_data.query,
        channel_id=search_data.channel_id,
        top_k=search_data.top_k
    )
    
    # Verify user has access to each result's channel
    channel_service = ChannelService(db)
    filtered_results = []
    
    for result in results:
        if channel_service.verify_channel_access(result["channel_id"], user["id"]):
            filtered_results.append(SearchResult(**result))
    
    return filtered_results

@router.get("/summarize/{channel_id}")
async def summarize_channel(
    channel_id: int,
    limit: int = Query(100, ge=10, le=500, description="Number of messages to summarize"),
    user: dict = Depends(get_token_user),
    db: Session = Depends(get_db)
):
    """
    Generate a summary of recent channel messages.
    
    Returns a streaming response with bullet points.
    User must be a member of the channel.
    """
    # Verify user has access to channel
    channel_service = ChannelService(db)
    if not channel_service.verify_channel_access(channel_id, user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this channel's server"
        )
    
    ai_service = AIService(db)
    
    return StreamingResponse(
        ai_service.summarize_channel(channel_id, limit),
        media_type="text/plain",
        headers={
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-cache"
        }
    )

# Admin endpoint to reindex messages (useful if index gets corrupted)
@router.post("/reindex/{channel_id}")
async def reindex_channel(
    channel_id: int,
    user: dict = Depends(get_token_user),
    db: Session = Depends(get_db)
):
    """
    Reindex all messages in a channel (admin only).
    """
    # Check if user is admin/owner of the server
    channel_service = ChannelService(db)
    channel = channel_service.get_channel_by_id(channel_id)
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )
    
    server_service = ServerService(db)
    role = server_service.get_user_role(channel["server_id"], user["id"])
    
    if role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get all messages in channel
    messages = db.query(Message).filter(Message.channel_id == channel_id).all()
    
    # Reindex each message
    ai_service = AIService(db)
    success_count = 0
    
    for msg in messages:
        if await ai_service.embed_message(msg.id, msg.content):
            success_count += 1
    
    return {
        "message": f"Reindexed {success_count}/{len(messages)} messages",
        "channel_id": channel_id
    }