"""
Base model configuration.
Now imports from infra to avoid circular imports.
"""
from infra.database import Base, engine, SessionLocal

# Re-export everything that other modules might need
__all__ = ["Base", "engine", "SessionLocal"]