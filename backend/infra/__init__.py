"""
Infrastructure package initialization.
Exposes database, Redis, and vector store components.
"""
from .database import Base, engine, SessionLocal
from .redis_client import (
    init_redis,
    get_redis,
    ping_redis,
    publish,
    subscribe,
    set_key,
    get_key,
    delete_key,
)
from .vector_store import (
    init_index,
    add_embedding,
    search,
    save_index,
    load_index,
    get_index_stats,
    FAISS_AVAILABLE,
    EMBEDDING_DIM,
)

__all__ = [
    # Database
    "Base",
    "engine",
    "SessionLocal",
    
    # Redis
    "init_redis",
    "get_redis",
    "ping_redis",
    "publish",
    "subscribe",
    "set_key",
    "get_key",
    "delete_key",
    
    # Vector Store
    "init_index",
    "add_embedding",
    "search",
    "save_index",
    "load_index",
    "get_index_stats",
    "FAISS_AVAILABLE",
    "EMBEDDING_DIM",
]