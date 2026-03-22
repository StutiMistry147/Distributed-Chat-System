"""
Routes package initialization.
Creates the main API router and includes all route modules.
"""
from fastapi import APIRouter

# Import all route modules
from . import auth
from . import servers
from . import channels
from . import messages
from . import websocket
from . import ai

# Create main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router)
api_router.include_router(servers.router)
api_router.include_router(channels.router)
api_router.include_router(messages.router)
api_router.include_router(websocket.router)
api_router.include_router(ai.router)

# Export the router
__all__ = ["api_router"]