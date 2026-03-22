"""
Vector store infrastructure module.
Handles FAISS index for semantic search embeddings.
"""
import os
import json
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Try to import FAISS, but don't crash if not available
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("⚠️ FAISS not installed. Vector search disabled.")

# Configuration
EMBEDDING_DIM = 384  # Dimension for all-MiniLM-L6-v2 model
DEFAULT_INDEX_PATH = os.getenv("VECTOR_INDEX_PATH", "./data/faiss.index")
DEFAULT_MAPPING_PATH = os.getenv("VECTOR_MAPPING_PATH", "./data/mapping.pkl")

# Global FAISS index and mapping
_index: Optional['faiss.Index'] = None
_id_to_position: Dict[int, int] = {}  # message_id -> position in index
_position_to_id: Dict[int, int] = {}  # position -> message_id

def init_index(dim: int = EMBEDDING_DIM) -> bool:
    """Initialize a new FAISS index"""
    global _index
    if not FAISS_AVAILABLE:
        return False
    
    try:
        _index = faiss.IndexFlatL2(dim)  # L2 distance index
        logger.info(f"✅ FAISS index initialized with dimension {dim}")
        return True
    except Exception as e:
        logger.error(f"❌ FAISS initialization failed: {e}")
        return False

def add_embedding(message_id: int, vector: List[float]) -> bool:
    """
    Add an embedding to the index.
    
    Args:
        message_id: Database ID of the message
        vector: Embedding vector (list of floats)
    
    Returns:
        True if added successfully, False otherwise
    """
    global _index, _id_to_position, _position_to_id
    
    if not FAISS_AVAILABLE or _index is None:
        return False
    
    try:
        # Convert to numpy array and reshape for FAISS
        np_vector = np.array(vector, dtype=np.float32).reshape(1, -1)
        
        # Get current position (before adding)
        position = _index.ntotal
        
        # Add to index
        _index.add(np_vector)
        
        # Update mappings
        _id_to_position[message_id] = position
        _position_to_id[position] = message_id
        
        return True
    except Exception as e:
        logger.error(f"Failed to add embedding for message {message_id}: {e}")
        return False

def search(query_vector: List[float], top_k: int = 10) -> List[Dict]:
    """
    Search for similar embeddings.
    
    Args:
        query_vector: Query embedding vector
        top_k: Number of results to return
    
    Returns:
        List of dictionaries with message_id and similarity score
        Example: [{"message_id": 123, "score": 0.95}, ...]
    """
    global _index, _position_to_id
    
    if not FAISS_AVAILABLE or _index is None or _index.ntotal == 0:
        return []
    
    try:
        # Convert to numpy array
        np_query = np.array(query_vector, dtype=np.float32).reshape(1, -1)
        
        # Search
        k = min(top_k, _index.ntotal)
        distances, indices = _index.search(np_query, k)
        
        # Convert results
        results = []
        for i in range(k):
            position = indices[0][i]
            distance = distances[0][i]
            message_id = _position_to_id.get(position)
            if message_id:
                # Convert distance to similarity score (1 / (1 + distance))
                # This maps distance (0 to infinity) to score (1 to 0)
                similarity = 1.0 / (1.0 + distance)
                results.append({
                    "message_id": message_id,
                    "score": float(similarity)  # Ensure it's a float, not numpy type
                })
        
        return results
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return []

def save_index(index_path: str = DEFAULT_INDEX_PATH, mapping_path: str = DEFAULT_MAPPING_PATH) -> bool:
    """Save FAISS index and mappings to disk"""
    global _index, _id_to_position, _position_to_id
    
    if not FAISS_AVAILABLE or _index is None:
        return False
    
    try:
        # Create directory for index if it doesn't exist
        dir_path = os.path.dirname(index_path)
        if dir_path:  # Only create if there's actually a directory path
            os.makedirs(dir_path, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(_index, index_path)
        
        # Create directory for mapping if needed
        mapping_dir = os.path.dirname(mapping_path)
        if mapping_dir:
            os.makedirs(mapping_dir, exist_ok=True)
        
        # Save mappings - convert to serializable format
        mappings = {
            "id_to_position": _id_to_position,
            "position_to_id": {str(k): v for k, v in _position_to_id.items()}  # Convert int keys to strings for JSON
        }
        with open(mapping_path, 'w') as f:
            json.dump(mappings, f)
        
        logger.info(f"✅ Saved index to {index_path} and mappings to {mapping_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save index: {e}")
        return False

def load_index(index_path: str = DEFAULT_INDEX_PATH, mapping_path: str = DEFAULT_MAPPING_PATH) -> bool:
    """Load FAISS index and mappings from disk"""
    global _index, _id_to_position, _position_to_id
    
    if not FAISS_AVAILABLE:
        return False
    
    try:
        # Check if files exist
        if not os.path.exists(index_path) or not os.path.exists(mapping_path):
            logger.info(f"No existing index found at {index_path}")
            return init_index()
        
        # Load FAISS index
        _index = faiss.read_index(index_path)
        
        # Load mappings
        with open(mapping_path, 'r') as f:
            mappings = json.load(f)
        
        _id_to_position = {int(k): v for k, v in mappings["id_to_position"].items()}
        _position_to_id = {int(k): v for k, v in mappings["position_to_id"].items()}
        
        logger.info(f"✅ Loaded index from {index_path} with {_index.ntotal} vectors")
        return True
    except Exception as e:
        logger.error(f"Failed to load index: {e}")
        return init_index()  # Fall back to new index

def get_index_stats() -> Dict:
    """Get statistics about the current index"""
    global _index
    
    if not FAISS_AVAILABLE or _index is None:
        return {"status": "unavailable", "vector_count": 0}
    
    return {
        "status": "available",
        "vector_count": _index.ntotal,
        "dimension": _index.d,
        "is_trained": _index.is_trained
    }

__all__ = [
    "init_index",
    "add_embedding",
    "search",
    "save_index",
    "load_index",
    "get_index_stats",
    "FAISS_AVAILABLE",
    "EMBEDDING_DIM"
]