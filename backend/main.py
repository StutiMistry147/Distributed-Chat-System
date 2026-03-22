import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn
from contextlib import asynccontextmanager
import logging

# Load environment variables at startup
load_dotenv()

# Import the app factory from api package
from api import create_app

# Import models for table creation
from models import Base, engine

# Import AI service
from services import AIService, EMBEDDINGS_AVAILABLE, SUMMARIZATION_AVAILABLE

# Configure logging - convert string to logging constant
log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown lifecycle.
    """
    # Startup
    print("""
    ╔════════════════════════════════════════╗
    ║   Distributed Chat System - Backend    ║
    ║         Server Starting...              ║
    ╚════════════════════════════════════════╝
    """)
    print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    
    # Create database tables
    print("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully")
    except Exception as e:
        print(f"❌ Database table creation failed: {e}")
        print("   Check your DATABASE_URL in .env file")
    
    # Initialize Redis
    redis_available = False
    try:
        from infra import init_redis, ping_redis
        redis_client = init_redis()
        if redis_client and ping_redis():
            print("✅ Redis connected successfully")
            redis_available = True
        else:
            print("⚠️ Redis not available - running without cross-server communication")
    except ImportError:
        print("⚠️ Redis client not installed - run: pip install redis")
    except Exception as e:
        print(f"⚠️ Redis initialization failed: {e}")

    # Load vector index
    faiss_available = False
    try:
        from infra import load_index, get_index_stats, FAISS_AVAILABLE
        faiss_available = FAISS_AVAILABLE
        
        if faiss_available:
            load_index()
            stats = get_index_stats()
            print(f"✅ Vector index loaded: {stats['vector_count']} vectors")
        else:
            print("⚠️ FAISS not installed - vector search disabled")
    except ImportError:
        print("⚠️ FAISS not installed - run: pip install faiss-cpu")
        faiss_available = False
    except Exception as e:
        print(f"⚠️ Vector index loading failed: {e}")
        # Initialize new index
        try:
            from infra import init_index
            if init_index():
                print("✅ New vector index initialized")
            else:
                print("❌ Failed to initialize vector index")
        except Exception as e2:
            print(f"❌ Vector index initialization failed: {e2}")
    
    # Preload AI model (optional - just to warm up)
    try:
        # embed_text doesn't need a DB session for model loading
        ai_service = AIService(None)
        ai_service.embed_text("warmup")
        print("✅ AI model loaded successfully")
    except ImportError:
        print("⚠️ AI service not available - missing dependencies")
    except Exception as e:
        print(f"⚠️ AI model preload skipped: {e}")
    
    print("\n🚀 Server ready to accept connections\n")
    
    yield
    
    # Shutdown
    print("\n🛑 Shutting down server...")
    
    # Save vector index before shutdown
    if faiss_available:
        try:
            from infra import save_index
            if save_index():
                print("✅ Vector index saved")
            else:
                print("⚠️ Failed to save vector index")
        except Exception as e:
            print(f"⚠️ Error saving vector index: {e}")
    
    # Close Redis connection
    if redis_available:
        try:
            from infra import get_redis
            redis_client = get_redis()
            if redis_client:
                redis_client.close()
                print("✅ Redis connection closed")
        except Exception as e:
            print(f"⚠️ Error closing Redis connection: {e}")
    
    print("👋 Goodbye!")

# Create FastAPI instance using the factory with lifespan
app = create_app(lifespan=lifespan)

# Root health check
@app.get("/")
async def root():
    """
    Simple health check endpoint.
    Returns server status and configuration info.
    """
    # Check infrastructure status
    infra_status = {}
    
    # Check Redis
    try:
        from infra import ping_redis
        infra_status["redis"] = "connected" if ping_redis() else "disconnected"
    except:
        infra_status["redis"] = "unavailable"
    
    # Check FAISS
    try:
        from infra import get_index_stats, FAISS_AVAILABLE
        if FAISS_AVAILABLE:
            stats = get_index_stats()
            infra_status["vector_store"] = f"available ({stats['vector_count']} vectors)"
        else:
            infra_status["vector_store"] = "not_installed"
    except:
        infra_status["vector_store"] = "unavailable"
    
    # Check AI service
    try:
        ai_status = []
        if EMBEDDINGS_AVAILABLE:
            ai_status.append("embeddings")
        if SUMMARIZATION_AVAILABLE:
            ai_status.append("summarization")
        infra_status["ai"] = ", ".join(ai_status) if ai_status else "disabled"
    except:
        infra_status["ai"] = "unavailable"
    
    return {
        "service": "Distributed Chat System API",
        "version": "0.1.0",
        "status": "operational",
        "mode": "database connected",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "infrastructure": infra_status,
        "endpoints": {
            "auth": "/api/auth",
            "servers": "/api/servers",
            "channels": "/api/channels",
            "messages": "/api/messages",
            "websocket": "/api/ws/{channel_id}",
            "ai_search": "/api/ai/search",
            "ai_summarize": "/api/ai/summarize/{channel_id}"
        }
    }

# Detailed health check for monitoring systems
@app.get("/health")
async def health():
    """
    Detailed health check for monitoring systems.
    Returns component statuses with timestamps.
    """
    # Check database
    db_status = "unknown"
    try:
        from sqlalchemy import text
        from models.base import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Check Redis
    redis_status = "unknown"
    try:
        from infra import ping_redis
        redis_status = "healthy" if ping_redis() else "disconnected"
    except:
        redis_status = "not_configured"
    
    # Check FAISS
    vector_status = "unknown"
    vector_count = 0
    try:
        from infra import get_index_stats, FAISS_AVAILABLE
        if FAISS_AVAILABLE:
            stats = get_index_stats()
            vector_status = "healthy" if stats["status"] == "available" else "unavailable"
            vector_count = stats["vector_count"]
        else:
            vector_status = "not_installed"
    except:
        vector_status = "error"
    
    # Check AI service
    ai_status = "unknown"
    try:
        if EMBEDDINGS_AVAILABLE and SUMMARIZATION_AVAILABLE:
            ai_status = "healthy"
        elif EMBEDDINGS_AVAILABLE or SUMMARIZATION_AVAILABLE:
            ai_status = "partial"
        else:
            ai_status = "disabled"
    except:
        ai_status = "unavailable"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "api": {
                "status": "up",
                "version": "0.1.0"
            },
            "database": {
                "status": db_status
            },
            "redis": {
                "status": redis_status
            },
            "vector_store": {
                "status": vector_status,
                "vector_count": vector_count
            },
            "ai_service": {
                "status": ai_status
            }
        }
    }

# Run the server
if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    # Start server with hot reload in development
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("ENVIRONMENT", "development") == "development",
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )