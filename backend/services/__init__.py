"""
Services package initialization.
Exposes all service classes for easy importing from the services package.
"""
from .auth_service import AuthService
from .server_service import ServerService
from .channel_service import ChannelService
from .message_service import MessageService
from .presence_service import PresenceService
from .ai_service import AIService, background_embed_message, EMBEDDINGS_AVAILABLE, SUMMARIZATION_AVAILABLE

__all__ = [
    "AuthService",
    "ServerService",
    "ChannelService", 
    "MessageService",
    "PresenceService",
    "AIService",
    "background_embed_message",
    "EMBEDDINGS_AVAILABLE",
    "SUMMARIZATION_AVAILABLE"
]