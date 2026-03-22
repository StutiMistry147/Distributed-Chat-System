from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from ..dependencies import get_token_user, get_db
from services import ServerService
from models.enums import MemberRole

router = APIRouter(prefix="/servers", tags=["servers"])

# Request/Response Models
class ServerCreate(BaseModel):
    name: str
    max_message_length: Optional[int] = 2000

class ServerJoin(BaseModel):
    invite_code: str

class ServerResponse(BaseModel):
    id: int
    name: str
    invite_code: str
    member_count: int
    owner_id: Optional[int] = None

class ServerMemberResponse(BaseModel):
    id: int
    username: str
    role: str
    presence_status: str

@router.post("", response_model=ServerResponse, status_code=status.HTTP_201_CREATED)
async def create_server(
    server_data: ServerCreate,
    user: dict = Depends(get_token_user),
    db: Session = Depends(get_db)
):
    """
    Create a new server.
    
    Accepts server name, creates it under the current user as owner.
    Returns the created server details.
    """
    server_service = ServerService(db)
    server = server_service.create_server(
        name=server_data.name,
        owner_id=user["id"],
        max_message_length=server_data.max_message_length
    )
    
    return ServerResponse(
        id=server["id"],
        name=server["name"],
        invite_code=server["invite_code"],
        member_count=server["member_count"],
        owner_id=server["owner_id"]
    )

@router.get("", response_model=List[ServerResponse])
async def get_user_servers(
    user: dict = Depends(get_token_user),
    db: Session = Depends(get_db)
):
    """
    Get all servers the current user belongs to.
    
    Returns a list of servers where the user is a member.
    Note: owner_id is not included in this list response.
    To get owner info, use the individual server endpoint.
    """
    server_service = ServerService(db)
    servers = server_service.get_user_servers(user["id"])
    
    return [ServerResponse(
        id=s["id"],
        name=s["name"],
        invite_code=s["invite_code"],
        member_count=s["member_count"],
        owner_id=None  # Not included in list view
    ) for s in servers]

@router.post("/join", response_model=ServerResponse)
async def join_server(
    join_data: ServerJoin,
    user: dict = Depends(get_token_user),
    db: Session = Depends(get_db)
):
    """
    Join an existing server via invite code.
    
    Accepts an invite code and adds the current user to that server.
    Returns the joined server details.
    """
    server_service = ServerService(db)
    
    # Find server by invite code
    server = server_service.get_server_by_invite_code(join_data.invite_code)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid invite code"
        )
    
    # Add user to server
    membership = server_service.add_user_to_server(
        server_id=server["id"],
        user_id=user["id"],
        role=MemberRole.MEMBER
    )
    
    return ServerResponse(
        id=server["id"],
        name=server["name"],
        invite_code=server["invite_code"],
        member_count=membership["member_count"],
        owner_id=None
    )

@router.get("/{server_id}/members", response_model=List[ServerMemberResponse])
async def get_server_members(
    server_id: int,
    user: dict = Depends(get_token_user),
    db: Session = Depends(get_db)
):
    """
    Get all members of a specific server.
    
    Returns a list of users who are members of the server.
    User must be a member of the server to view its members.
    """
    server_service = ServerService(db)
    
    # Check if user is a member
    if not server_service.is_member(server_id, user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this server"
        )
    
    members = server_service.get_server_members(server_id)
    
    return [ServerMemberResponse(
        id=m["id"],
        username=m["username"],
        role=m["role"],
        presence_status=m["presence_status"]
    ) for m in members]