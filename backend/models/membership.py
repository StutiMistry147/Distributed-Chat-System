from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
from .enums import MemberRole

class Membership(Base):
    __tablename__ = "memberships"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    server_id = Column(Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    role = Column(Enum(MemberRole), default=MemberRole.MEMBER, nullable=False)
    
    # A user cannot be in the same server twice
    __table_args__ = (
        UniqueConstraint('user_id', 'server_id', name='unique_user_server'),
    )
    
    # Relationships
    user = relationship("User", back_populates="memberships")
    server = relationship("Server", back_populates="memberships")
    
    def __repr__(self):
        return f"<Membership(user_id={self.user_id}, server_id={self.server_id}, role='{self.role}')>"