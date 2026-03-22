from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from ..dependencies import get_token_user, get_db
from services import ChannelService, ServerService

router = APIRouter(prefix="/channels", tags=["channels"])

# Request/Response Models
class ChannelCreate(BaseModel):
    name: str
    server_id: int

class ChannelResponse(BaseModel):
    id: int
    name: str
    server_id: int

@router.post("", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(
    channel_data: ChannelCreate,
    user: dict = Depends(get_token_user),
    db: Session = Depends(get_db)
):
    """
    Create a new channel inside a server.
    
    Accepts channel name and server ID. User must be a member of the server.
    Returns the created channel details.
    """
    # Verify user is member of the server
    server_service = ServerService(db)
    if not server_service.is_member(channel_data.server_id, user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this server"
        )
    
    # Create channel
    channel_service = ChannelService(db)
    channel = channel_service.create_channel(
        name=channel_data.name,
        server_id=channel_data.server_id,
        user_id=user["id"]  # Pass user_id for permission checks
    )
    
    return ChannelResponse(
        id=channel["id"],
        name=channel["name"],
        server_id=channel["server_id"]
    )

@router.get("/server/{server_id}", response_model=List[ChannelResponse])
async def get_server_channels(
    server_id: int,
    user: dict = Depends(get_token_user),
    db: Session = Depends(get_db)
):
    """
    Get all channels that belong to a specific server.
    
    User must be a member of the server to view its channels.
    Returns a list of channels in the server.
    """
    # Verify user is member of the server
    server_service = ServerService(db)
    if not server_service.is_member(server_id, user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this server"
        )
    
    # Get channels
    channel_service = ChannelService(db)
    channels = channel_service.get_server_channels(server_id)
    
    return [ChannelResponse(
        id=c["id"],
        name=c["name"],
        server_id=c["server_id"]
    ) for c in channels]

@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(
    channel_id: int,
    user: dict = Depends(get_token_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific channel.
    
    User must be a member of the parent server.
    Returns channel details.
    """
    channel_service = ChannelService(db)
    
    # Verify user has access to channel
    if not channel_service.verify_channel_access(channel_id, user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this channel's server"
        )
    
    channel = channel_service.get_channel_by_id(channel_id)
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )
    
    return ChannelResponse(
        id=channel["id"],
        name=channel["name"],
        server_id=channel["server_id"]
    )