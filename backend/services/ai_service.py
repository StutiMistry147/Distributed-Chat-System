"""
AI Service for semantic search and channel summarization.
Completely decoupled from core chat - failures here don't affect messaging.
"""
import asyncio
import numpy as np
from typing import List, Dict, Optional, AsyncGenerator
from sqlalchemy.orm import Session
import logging
from datetime import datetime
import os

# Try to load sentence-transformers - fail gracefully if not available
try:
    from sentence_transformers import SentenceTransformer # type : ignore
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    logging.warning("⚠️ sentence-transformers not installed. Semantic search disabled.")

# Try to load google-genai (new package) - fail gracefully if not available
try:
    from google import genai
    SUMMARIZATION_AVAILABLE = True
except ImportError:
    SUMMARIZATION_AVAILABLE = False
    logging.warning("⚠️ google-genai not installed. Channel summarization disabled.")

from infra.vector_store import add_embedding, search, FAISS_AVAILABLE, EMBEDDING_DIM
from models import Message
from models.base import SessionLocal

logger = logging.getLogger(__name__)

# Global model instance (loaded once at startup)
_model = None

class AIService:
    def __init__(self, db: Session):
        self.db = db
        
    # ========== Embedding Methods ==========
    
    def _ensure_model_loaded(self):
        """Load the sentence transformer model on first use"""
        global _model
        if _model is None and EMBEDDINGS_AVAILABLE:
            try:
                model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
                logger.info(f"Loading embedding model: {model_name}")
                _model = SentenceTransformer(model_name)
                logger.info("✅ Embedding model loaded successfully")
            except Exception as e:
                logger.error(f"❌ Failed to load embedding model: {e}")
                return False
        return _model is not None
    
    def embed_text(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text string.
        Returns None if embeddings unavailable.
        """
        if not EMBEDDINGS_AVAILABLE or not self._ensure_model_loaded():
            return None
        
        try:
            embedding = _model.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    async def embed_message(self, message_id: int, content: str) -> bool:
        """
        Generate and store embedding for a message.
        Called as background task after message save.
        """
        if not FAISS_AVAILABLE:
            logger.debug("FAISS not available, skipping embedding")
            return False
        
        # Run embedding in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(None, self.embed_text, content)
        
        if embedding is None:
            return False
        
        # Store in FAISS
        return add_embedding(message_id, embedding)
    
    def search_similar(self, query: str, channel_id: Optional[int] = None, top_k: int = 10) -> List[Dict]:
        """
        Search for messages similar to the query.
        
        Args:
            query: Natural language query
            channel_id: Optional channel to restrict search to
            top_k: Number of results to return
        
        Returns:
            List of messages with similarity scores
        """
        if not FAISS_AVAILABLE or not EMBEDDINGS_AVAILABLE:
            return []
        
        # Generate query embedding
        query_embedding = self.embed_text(query)
        if query_embedding is None:
            return []
        
        # Search FAISS
        results = search(query_embedding, top_k * 2)  # Get extra to filter by channel
        
        if not results:
            return []
        
        # Get message IDs
        message_ids = [r["message_id"] for r in results]
        
        # Fetch messages from database
        query = self.db.query(Message).filter(Message.id.in_(message_ids))
        
        # Filter by channel if specified
        if channel_id:
            query = query.filter(Message.channel_id == channel_id)
        
        messages = query.all()
        
        # Create score lookup
        score_map = {r["message_id"]: r["score"] for r in results}
        
        # Build response
        response = []
        for msg in messages:
            response.append({
                "id": msg.id,
                "content": msg.content,
                "username": msg.username,
                "user_id": msg.user_id,
                "channel_id": msg.channel_id,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                "score": score_map.get(msg.id, 0)
            })
        
        # Sort by score descending
        response.sort(key=lambda x: x["score"], reverse=True)
        
        return response[:top_k]
    
    # ========== Summarization Methods ==========
    
    async def summarize_channel(
        self,
        channel_id: int,
        limit: int = 100,
        model: str = "gemini-2.0-flash-lite"
    ) -> AsyncGenerator[str, None]:
        """
        Generate a summary of recent channel messages.
        Streams response chunks as they arrive from Gemini.
        
        Uses google-genai package (new version).
        """
        if not SUMMARIZATION_AVAILABLE:
            yield "❌ Summarization unavailable - google-genai package not installed"
            return
        
        # Get recent messages
        messages = self.db.query(Message)\
            .filter(Message.channel_id == channel_id)\
            .order_by(Message.timestamp.desc())\
            .limit(limit)\
            .all()
        
        # Reverse to chronological order
        messages.reverse()
        
        if not messages:
            yield "No messages found in this channel."
            return
        
        # Format messages for Gemini
        formatted = []
        for msg in messages:
            timestamp = msg.timestamp.strftime("%H:%M") if msg.timestamp else "unknown"
            formatted.append(f"[{timestamp}] {msg.username}: {msg.content}")
        
        conversation = "\n".join(formatted)
        
        # Create prompt
        prompt = f"""Please provide a concise summary of the following chat conversation in 5 bullet points. 
Focus on the main topics discussed, key questions asked, and any decisions made.

Channel conversation:
{conversation}

Summary (5 bullet points):"""
        
        # Call Gemini API
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            yield "❌ GOOGLE_API_KEY not set in environment"
            return
        
        client = genai.Client(api_key=api_key)
        
        try:
            # Use the new genai package API
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config={
                    'temperature': 0.7,
                    'max_output_tokens': 500,
                }
            )
            
            # Gemini doesn't stream by default in the new package
            # Yield the full response as one chunk
            if response.text:
                yield response.text
            else:
                yield "No summary generated."
                    
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            yield f"❌ Summarization failed: {str(e)}"
    
    async def quick_summary(self, channel_id: int, limit: int = 50) -> str:
        """
        Non-streaming version for simple use cases.
        """
        chunks = []
        async for chunk in self.summarize_channel(channel_id, limit):
            chunks.append(chunk)
        return "".join(chunks)


# Standalone functions for background tasks - creates its own DB session
async def background_embed_message(message_id: int, content: str):
    """
    Standalone function to be called as background task.
    Creates its own database session to avoid issues with closed sessions.
    """
    db = SessionLocal()
    try:
        ai_service = AIService(db)
        await ai_service.embed_message(message_id, content)
    except Exception as e:
        logger.error(f"Background embedding failed for message {message_id}: {e}")
    finally:
        db.close()


# Export constants
__all__ = [
    "AIService",
    "background_embed_message",
    "EMBEDDINGS_AVAILABLE",
    "SUMMARIZATION_AVAILABLE"
]