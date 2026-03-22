from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from models import Server, Membership, User
from models.enums import MemberRole
from fastapi import HTTPException, status
import secrets
from typing import List, Optional

class ServerService:
    def __init__(self, db: Session):
        self.db = db
    
    def _generate_invite_code(self) -> str:
        """Generate a unique invite code"""
        while True:
            code = secrets.token_urlsafe(8)
            # Check if code already exists
            existing = self.db.query(Server).filter(Server.invite_code == code).first()
            if not existing:
                return code
    
    def create_server(self, name: str, owner_id: int, max_message_length: int = 2000) -> dict:
        """
        Create a new server with the user as owner.
        
        Creates server record and owner membership in a single transaction.
        """
        # Generate unique invite code
        invite_code = self._generate_invite_code()
        
        # Create server
        server = Server(
            name=name,
            invite_code=invite_code,
            max_message_length=max_message_length
        )
        self.db.add(server)
        self.db.flush()  # Get server.id without committing
        
        # Create owner membership
        membership = Membership(
            user_id=owner_id,
            server_id=server.id,
            role=MemberRole.OWNER
        )
        self.db.add(membership)
        
        # Commit transaction
        self.db.commit()
        
        return {
            "id": server.id,
            "name": server.name,
            "invite_code": server.invite_code,
            "owner_id": owner_id,
            "member_count": 1,
            "created_at": server.created_at.isoformat() if server.created_at else None
        }
    

    def get_user_servers(self, user_id: int) -> List[dict]:
        """Get all servers a user is a member of"""
        servers = self.db.query(Server)\
            .join(Membership)\
            .filter(Membership.user_id == user_id)\
            .all()
        
        result = []
        for server in servers:
            # TODO: Optimize this - currently N+1 queries
            # For production, use a single query with JOIN and COUNT
            member_count = self.db.query(Membership)\
                .filter(Membership.server_id == server.id)\
                .count()
            
            result.append({
                "id": server.id,
                "name": server.name,
                "invite_code": server.invite_code,
                "member_count": member_count,
                "created_at": server.created_at.isoformat() if server.created_at else None
            })
        
        return result
    
    def get_server_by_id(self, server_id: int) -> Optional[dict]:
        """Get server details by ID"""
        server = self.db.query(Server).filter(Server.id == server_id).first()
        if not server:
            return None
        
        member_count = self.db.query(Membership)\
            .filter(Membership.server_id == server.id)\
            .count()
        
        # Find owner
        owner_membership = self.db.query(Membership)\
            .filter(
                and_(
                    Membership.server_id == server.id,
                    Membership.role == MemberRole.OWNER
                )
            ).first()
        
        return {
            "id": server.id,
            "name": server.name,
            "invite_code": server.invite_code,
            "owner_id": owner_membership.user_id if owner_membership else None,
            "member_count": member_count,
            "max_message_length": server.max_message_length,
            "created_at": server.created_at.isoformat() if server.created_at else None
        }
    
    def get_server_by_invite_code(self, invite_code: str) -> Optional[dict]:
        """Find server by invite code - used for joining"""
        server = self.db.query(Server)\
            .filter(Server.invite_code == invite_code)\
            .first()
        
        if not server:
            return None
        
        member_count = self.db.query(Membership)\
            .filter(Membership.server_id == server.id)\
            .count()
        
        return {
            "id": server.id,
            "name": server.name,
            "invite_code": server.invite_code,
            "member_count": member_count
        }
    
    def add_user_to_server(self, server_id: int, user_id: int, role: MemberRole = MemberRole.MEMBER) -> dict:
        """Add a user to a server (join via invite or direct add)"""
        # Check if already a member
        existing = self.db.query(Membership)\
            .filter(
                and_(
                    Membership.user_id == user_id,
                    Membership.server_id == server_id
                )
            ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already a member of this server"
            )
        
        # Add membership
        membership = Membership(
            user_id=user_id,
            server_id=server_id,
            role=role
        )
        self.db.add(membership)
        self.db.commit()
        
        # Get updated member count
        member_count = self.db.query(Membership)\
            .filter(Membership.server_id == server_id)\
            .count()
        
        return {
            "server_id": server_id,
            "user_id": user_id,
            "role": role.value,
            "joined_at": membership.joined_at.isoformat() if membership.joined_at else None,
            "member_count": member_count
        }
    
    def get_server_members(self, server_id: int) -> List[dict]:
        """Get all members of a server with their details"""
        memberships = self.db.query(Membership)\
            .options(joinedload(Membership.user))\
            .filter(Membership.server_id == server_id)\
            .all()
        
        result = []
        for membership in memberships:
            if membership.user:  # User might be deleted
                result.append({
                    "id": membership.user.id,
                    "username": membership.user.username,
                    "email": membership.user.email,
                    "role": membership.role.value,
                    "presence_status": membership.user.presence_status.value if membership.user.presence_status else "offline",
                    "joined_at": membership.joined_at.isoformat() if membership.joined_at else None
                })
        
        return result
    
    def is_member(self, server_id: int, user_id: int) -> bool:
        """Check if a user is a member of a server"""
        membership = self.db.query(Membership)\
            .filter(
                and_(
                    Membership.user_id == user_id,
                    Membership.server_id == server_id
                )
            ).first()
        return membership is not None
    
    def get_user_role(self, server_id: int, user_id: int) -> Optional[str]:
        """Get a user's role in a server"""
        membership = self.db.query(Membership)\
            .filter(
                and_(
                    Membership.user_id == user_id,
                    Membership.server_id == server_id
                )
            ).first()
        
        return membership.role.value if membership else None