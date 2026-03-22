# backend/models/enums.py
import enum

class PresenceStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    IDLE = "idle"
    VANISH = "vanish"

class MemberRole(str, enum.Enum):
    OWNER = "owner"  # Server creator/owner (only one per server)
    ADMIN = "admin"  # Can manage channels and members
    MEMBER = "member"  # Regular member

__all__ = ["PresenceStatus", "MemberRole"]