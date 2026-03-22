from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)  # Text type for longer messages, but we'll enforce length in validation
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    username = Column(String(50), nullable=False)  # Denormalized for historical accuracy
    channel_id = Column(Integer, ForeignKey("channels.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    is_edited = Column(Boolean, default=False, nullable=False)
    edited_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    # Use foreign_keys to specify which column to use for the relationship
    user = relationship("User", back_populates="messages", foreign_keys=[user_id])
    channel = relationship("Channel", back_populates="messages")
    
    # Composite index for common query patterns
    # For skeleton phase: simple composite index without order specification
    # Later we can create a more specific index with descending order using:
    # Index('ix_messages_channel_timestamp_desc', channel_id, timestamp.desc())
    __table_args__ = (
        Index('ix_messages_channel_timestamp', 'channel_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<Message(id={self.id}, user='{self.username}', channel={self.channel_id}, timestamp={self.timestamp})>"