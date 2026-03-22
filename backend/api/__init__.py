"""
API package initialization.
Exports the FastAPI app factory and shared dependencies.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional, Callable

# Import the main router from routes package
from .routes import api_router

# Import shared dependencies
from .routes.auth import get_current_user
from .dependencies import get_token_user, get_db

def create_app(lifespan: Optional[Callable] = None) -> FastAPI:
    """
    Factory function to create and configure the FastAPI application.
    
    Args:
        lifespan: Optional lifespan context manager
        
    Returns:
        Configured FastAPI application
    """
    app_kwargs = {
        "title": "Distributed Chat System",
        "description": "Real-time messaging platform with AI-powered features",
        "version": "0.1.0",
        "docs_url": "/api/docs",
        "redoc_url": "/api/redoc",
        "openapi_url": "/api/openapi.json"
    }
    
    if lifespan:
        app_kwargs["lifespan"] = lifespan
    
    app = FastAPI(**app_kwargs)
    
    # Configure CORS middleware - must be added before routes
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "https://distributed-chat-system-production.up.railway.app"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include all routes under /api prefix
    app.include_router(api_router, prefix="/api")
    
    return app

# Export shared dependencies for easy importing
__all__ = [
    "create_app",
    "get_current_user",
    "get_token_user",
    "get_db"
]