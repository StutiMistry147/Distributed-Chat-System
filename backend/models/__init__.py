"""
Models package initialization.
Import all models here so SQLAlchemy knows about them.
"""
from .base import Base, engine, SessionLocal
from .enums import PresenceStatus, MemberRole
from .user import User
from .server import Server
from .channel import Channel
from .message import Message
from .membership import Membership

# This ensures all models are imported and registered with SQLAlchemy
__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "PresenceStatus",
    "MemberRole",
    "User",
    "Server",
    "Channel",
    "Message",
    "Membership",
]