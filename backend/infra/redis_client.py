"""
Redis infrastructure module.
Handles Redis connection, pub/sub for cross-server communication, and presence tracking.
"""
import os
import json
import redis
from typing import Optional, Any, Dict
import logging

logger = logging.getLogger(__name__)

# Get Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Global Redis client instance
_redis_client: Optional[redis.Redis] = None

def init_redis() -> redis.Redis:
    """Initialize Redis client (called on startup)"""
    global _redis_client
    try:
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        # Test connection
        _redis_client.ping()
        logger.info("✅ Redis connected successfully")
        return _redis_client
    except redis.ConnectionError as e:
        logger.warning(f"⚠️ Redis connection failed: {e}. Running without Redis.")
        _redis_client = None
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected Redis error: {e}")
        _redis_client = None
        return None

def get_redis() -> Optional[redis.Redis]:
    """Get Redis client instance (for FastAPI dependencies)"""
    global _redis_client
    if _redis_client is None:
        # WARNING: This has a race condition if multiple requests arrive
        # before Redis is initialized. In production, consider using:
        # - A proper connection pool
        # - Initializing Redis at startup (already done in main.py)
        # - Using a lock if lazy initialization is required
        return init_redis()
    return _redis_client

def ping_redis() -> bool:
    """Test Redis connection, return True if available"""
    client = get_redis()
    if not client:
        return False
    try:
        return client.ping()
    except:
        return False

def publish(channel: str, message: Dict[str, Any]) -> bool:
    """
    Publish a message to a Redis channel.
    
    Args:
        channel: Channel name (e.g., "server:123", "presence")
        message: Dictionary to publish (will be JSON encoded)
    
    Returns:
        True if published successfully, False otherwise
    """
    client = get_redis()
    if not client:
        return False
    
    try:
        message_json = json.dumps(message, default=str)
        client.publish(channel, message_json)
        return True
    except Exception as e:
        logger.error(f"Redis publish failed: {e}")
        return False

def subscribe(channel: str) -> Optional[redis.client.PubSub]:
    """
    Subscribe to a Redis channel.
    
    Args:
        channel: Channel name to subscribe to
    
    Returns:
        PubSub object or None if Redis unavailable
    """
    client = get_redis()
    if not client:
        return None
    
    try:
        pubsub = client.pubsub()
        pubsub.subscribe(channel)
        return pubsub
    except Exception as e:
        logger.error(f"Redis subscribe failed: {e}")
        return None

def set_key(key: str, value: Any, expiry: Optional[int] = None) -> bool:
    """Set a key in Redis (for presence tracking)"""
    client = get_redis()
    if not client:
        return False
    
    try:
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        if expiry:
            client.setex(key, expiry, value)
        else:
            client.set(key, value)
        return True
    except Exception as e:
        logger.error(f"Redis set failed: {e}")
        return False

def get_key(key: str) -> Optional[str]:
    """Get a key from Redis"""
    client = get_redis()
    if not client:
        return None
    
    try:
        return client.get(key)
    except Exception as e:
        logger.error(f"Redis get failed: {e}")
        return None

def delete_key(key: str) -> bool:
    """Delete a key from Redis"""
    client = get_redis()
    if not client:
        return False
    
    try:
        client.delete(key)
        return True
    except Exception as e:
        logger.error(f"Redis delete failed: {e}")
        return False

__all__ = [
    "init_redis",
    "get_redis", 
    "ping_redis",
    "publish",
    "subscribe",
    "set_key",
    "get_key",
    "delete_key"
]