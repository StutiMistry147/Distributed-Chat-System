from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class Server(Base):
    __tablename__ = "servers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    # owner_id removed - ownership is now determined by Membership.role = 'owner'
    invite_code = Column(String(50), unique=True, nullable=False, index=True)
    max_message_length = Column(Integer, default=2000, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('max_message_length >= 1 AND max_message_length <= 10000', 
                       name='check_max_message_length'),
    )
    
    # Relationships
    memberships = relationship("Membership", back_populates="server", cascade="all, delete-orphan")
    channels = relationship("Channel", back_populates="server", cascade="all, delete-orphan")
    
    @property
    def member_count(self):
        """
        WARNING: This property loads all memberships into memory.
        For production, use a SQL COUNT query instead:
        db.query(Membership).filter(Membership.server_id == self.id).count()
        """
        return len(self.memberships) if self.memberships else 0
    
    @property
    def owner(self):
        """Get the server owner from memberships"""
        for membership in self.memberships:
            if membership.role == "owner":
                return membership.user
        return None
    
    def __repr__(self):
        return f"<Server(id={self.id}, name='{self.name}')>"