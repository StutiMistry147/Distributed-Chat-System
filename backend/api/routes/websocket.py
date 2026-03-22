from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, Query, HTTPException, Depends
from typing import Dict, Set, Optional
from services.ai_service import background_embed_message
import asyncio
import json
from datetime import datetime
from sqlalchemy.orm import Session
from .auth import get_current_user
from ..dependencies import get_token_user, get_db
from services import MessageService, AuthService, PresenceService
from models.base import SessionLocal
import traceback

# Redis imports for distributed messaging
from infra.redis_client import publish, subscribe, set_key, delete_key

# AI Service import for background embedding
from services.ai_service import background_embed_message  # Moved to top level

router = APIRouter(prefix="/ws", tags=["websocket"])

# Connection Manager
class ConnectionManager:
    def __init__(self):
        # Active connections: {channel_id: {user_id: websocket}}
        self.active_connections: Dict[int, Dict[int, WebSocket]] = {}
        # User channels: {user_id: set(channel_ids)}
        self.user_channels: Dict[int, Set[int]] = {}
        # User info cache: {user_id: {"username": str}}
        self.user_info: Dict[int, Dict] = {}
        # Redis listener tasks: {channel_id: asyncio.Task}
        self.active_listeners: Dict[int, asyncio.Task] = {}
    
    async def connect(self, websocket: WebSocket, channel_id: int, user_id: int, username: str, db: Session):
        """Accept a WebSocket connection and register it"""
        await websocket.accept()
        
        # Initialize channel dict if needed
        if channel_id not in self.active_connections:
            self.active_connections[channel_id] = {}
        
        # Store connection
        self.active_connections[channel_id][user_id] = websocket
        
        # Track user's channels
        if user_id not in self.user_channels:
            self.user_channels[user_id] = set()
        self.user_channels[user_id].add(channel_id)
        
        # Cache user info
        self.user_info[user_id] = {"username": username}
        
        # Update last seen in database
        auth_service = AuthService(db)
        auth_service.update_last_seen(user_id)
        
        # Update presence to online in database
        presence_service = PresenceService(db)
        presence_service.update_presence(user_id, "online")
        
        # Set Redis presence with 5 minute expiry (acts as heartbeat)
        set_key(f"presence:{user_id}", "online", expiry=300)
        
        # Start Redis listener for this channel if not already running
        await self.start_redis_listener(channel_id)
        
        # Notify others that user joined
        await self.broadcast_to_channel(
            channel_id,
            {
                "type": "presence",
                "event": "join",
                "user_id": user_id,
                "username": username,
                "channel_id": channel_id,
                "timestamp": datetime.now().isoformat()
            },
            exclude_user_id=user_id
        )
    
    async def disconnect(self, channel_id: int, user_id: int, db: Session):
        """Remove a disconnected connection"""
        if channel_id in self.active_connections:
            if user_id in self.active_connections[channel_id]:
                del self.active_connections[channel_id][user_id]
            
            # Clean up empty channel
            if not self.active_connections[channel_id]:
                del self.active_connections[channel_id]
                
                # Stop Redis listener when last user leaves
                await self.stop_redis_listener(channel_id)
        
        # Remove from user's channels
        if user_id in self.user_channels:
            self.user_channels[user_id].discard(channel_id)
            if not self.user_channels[user_id]:
                del self.user_channels[user_id]
        
        # Remove Redis presence
        delete_key(f"presence:{user_id}")
        
        # Update presence in database
        # Only update to offline if user has no other connections
        if user_id not in self.user_channels:
            presence_service = PresenceService(db)
            presence_service.update_presence(user_id, "offline")
    
    async def start_redis_listener(self, channel_id: int):
        """Start a background task to listen for Redis messages on this channel"""
        # Don't start if already running
        if channel_id in self.active_listeners:
            return
        
        # Create and store the listener task
        task = asyncio.create_task(self._redis_listener_loop(channel_id))
        self.active_listeners[channel_id] = task
        print(f"Started Redis listener for channel {channel_id}")
    
    async def stop_redis_listener(self, channel_id: int):
        """Stop the Redis listener for a channel"""
        if channel_id in self.active_listeners:
            self.active_listeners[channel_id].cancel()
            del self.active_listeners[channel_id]
            print(f"Stopped Redis listener for channel {channel_id}")
    
    async def _redis_listener_loop(self, channel_id: int):
        """
        Background task that listens for messages from Redis and broadcasts them locally.
        Runs as long as the channel has active connections.
        
        Note: This uses synchronous Redis pubsub with asyncio.sleep to avoid blocking.
        For production with high message volume, consider aioredis for true async.
        """
        redis_channel = f"chat:{channel_id}"
        
        # Subscribe to Redis channel
        pubsub = subscribe(redis_channel)
        if not pubsub:
            print(f"Redis unavailable for channel {channel_id} - running in local-only mode")
            return
        
        print(f"Redis listener subscribed to {redis_channel}")
        
        try:
            # Listen while channel has active connections
            while channel_id in self.active_connections:
                # Check for messages (non-blocking, but brief sync pause)
                message = pubsub.get_message()
                
                if message and message['type'] == 'message':
                    try:
                        # Parse the message data
                        data = json.loads(message['data'])
                        
                        # Don't rebroadcast to the sender if they're on this instance
                        sender_id = data.get('sender_id')
                        
                        # Broadcast to local connections (excluding sender)
                        await self.broadcast_to_channel(
                            channel_id,
                            data,
                            exclude_user_id=sender_id
                        )
                    except json.JSONDecodeError:
                        print(f"Invalid JSON from Redis: {message['data']}")
                    except Exception as e:
                        print(f"Error processing Redis message: {e}")
                
                # Small sleep to avoid busy loop
                await asyncio.sleep(0.01)
                
        except asyncio.CancelledError:
            # Listener was cancelled - clean up
            print(f"Redis listener for channel {channel_id} cancelled")
            pubsub.close()
        except Exception as e:
            print(f"Redis listener error for channel {channel_id}: {e}")
        finally:
            # Ensure cleanup
            if channel_id in self.active_listeners:
                del self.active_listeners[channel_id]
    
    async def broadcast_to_channel(self, channel_id: int, message: dict, exclude_user_id: Optional[int] = None):
        """Broadcast a message to all users in a channel"""
        if channel_id not in self.active_connections:
            return
        
        # Create a copy of connections to safely iterate while potentially modifying
        connections = self.active_connections[channel_id].copy()
        
        # Convert message to JSON
        message_json = json.dumps(message, default=str)
        
        # Send to all connected users in the channel
        for user_id, connection in connections.items():
            if exclude_user_id and user_id == exclude_user_id:
                continue
            try:
                await connection.send_text(message_json)
            except Exception as e:
                # If send fails, connection might be dead - remove it
                print(f"Broadcast failed for user {user_id} in channel {channel_id}: {e}")
                await self.handle_broken_connection(channel_id, user_id)
    
    async def handle_broken_connection(self, channel_id: int, user_id: int):
        """Handle a broken WebSocket connection"""
        # Create a temporary DB session for the disconnect
        db = SessionLocal()
        try:
            await self.disconnect(channel_id, user_id, db)
        finally:
            db.close()
    
    async def broadcast_presence_update(self, user_id: int, status: str):
        """Broadcast presence update to all channels the user is in"""
        if user_id not in self.user_channels:
            return
        
        username = self.user_info.get(user_id, {}).get("username", "Unknown")
        
        for channel_id in self.user_channels[user_id]:
            await self.broadcast_to_channel(
                channel_id,
                {
                    "type": "presence",
                    "event": "update",
                    "user_id": user_id,
                    "username": username,
                    "status": status,
                    "timestamp": datetime.now().isoformat()
                }
            )

# Create global connection manager
manager = ConnectionManager()

@router.websocket("/{channel_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    channel_id: int,
    token: str = Query(..., description="JWT token for authentication")
):
    """
    WebSocket endpoint for real-time communication.
    
    Now with Redis integration for distributed messaging:
    - Messages are published to Redis after saving
    - Other server instances receive via Redis and broadcast locally
    - Sender gets immediate echo directly (no Redis round trip)
    """
    # Initialize variables to avoid UnboundLocalError in exception handlers
    user_id = None
    username = "unknown"
    
    # Create database session manually (can't use Depends in WebSocket)
    db = SessionLocal()
    
    try:
        # Authenticate user
        user = get_current_user(token, db)
        if not user:
            print(f"WebSocket connection rejected: Invalid token for channel {channel_id}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        user_id = user["id"]
        username = user["username"]
        
        # Accept connection and register
        await manager.connect(websocket, channel_id, user_id, username, db)
        print(f"WebSocket connected: User {username} (ID: {user_id}) joined channel {channel_id}")
        
        # Main message loop
        while True:
            # Wait for message from client
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                
                # Validate message
                if "content" not in message_data:
                    print(f"Invalid message format from user {user_id}: missing 'content' field")
                    continue
                
                content = message_data["content"]
                
                # Save message to database using service
                message_service = MessageService(db)
                try:
                    saved_message = message_service.save_message(
                        channel_id=channel_id,
                        user_id=user_id,
                        username=username,
                        content=content
                    )
                except ValueError as e:
                    # Validation error - send back to client
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "event": "invalid_message",
                        "message": str(e)
                    }))
                    continue
                
                print(f"Message persisted: ID {saved_message['id']} from user {username} in channel {channel_id}")
                
                # Update last seen
                auth_service = AuthService(db)
                auth_service.update_last_seen(user_id)
                
                # Create message object for broadcasting
                broadcast_message = {
                    "type": "message",
                    "event": "new",
                    "message": saved_message
                }
                
                # 1. Send immediate echo back to sender (no Redis round trip)
                await websocket.send_text(json.dumps(broadcast_message, default=str))
                
                # 2. Publish to Redis for all other server instances
                # Include sender_id so other instances know not to echo back to sender
                publish(
                    f"chat:{channel_id}",
                    {
                        **broadcast_message,
                        "sender_id": user_id  # So listeners can exclude the sender
                    }
                )
                
                # 3. Trigger AI embedding as background task (don't await)
                # Import is at top of file now
                asyncio.create_task(background_embed_message(
                    saved_message["id"],
                    saved_message["content"]
                ))
                
            except json.JSONDecodeError as e:
                # Invalid JSON - ignore
                print(f"Invalid JSON from user {user_id}: {e}")
                continue
                
    except WebSocketDisconnect:
        # Client disconnected
        print(f"WebSocket disconnected: User {username} (ID: {user_id}) left channel {channel_id}")
        await manager.disconnect(channel_id, user_id, db)
        
        # Notify others via Redis
        publish(f"chat:{channel_id}", {
            "type": "presence",
            "event": "leave",
            "user_id": user_id,
            "username": username,
            "channel_id": channel_id,
            "timestamp": datetime.now().isoformat(),
            "sender_id": user_id
        })
    except Exception as e:
        # Unexpected error - disconnect
        print(f"WebSocket error for user {username} (ID: {user_id}) in channel {channel_id}: {e}")
        print(traceback.format_exc())
        if user_id:  # Only try to disconnect if we had a valid user
            await manager.disconnect(channel_id, user_id, db)
    finally:
        # Always close the database session
        db.close()

# Additional endpoint for presence updates
@router.post("/presence/{presence_status}")
async def update_presence(
    presence_status: str,
    user: dict = Depends(get_token_user),
    db: Session = Depends(get_db)
):
    """
    Update user's presence status (online, offline, idle, vanish).
    Broadcasts the update to all channels the user is in via Redis.
    """
    valid_statuses = ["online", "offline", "idle", "vanish"]
    if presence_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    # Update presence in database
    presence_service = PresenceService(db)
    updated_user = presence_service.update_presence(user["id"], presence_status)
    
    # Update Redis presence
    if presence_status == "offline":
        delete_key(f"presence:{user['id']}")
    else:
        set_key(f"presence:{user['id']}", presence_status, expiry=300)
    
    print(f"Presence update: User {user['username']} (ID: {user['id']}) is now {presence_status}")
    
    # Broadcast to all channels via Redis
    await manager.broadcast_presence_update(user["id"], presence_status)
    
    return {"message": f"Presence updated to {presence_status}"}