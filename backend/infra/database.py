"""
Database infrastructure module.
Handles PostgreSQL connection, engine creation, and session management.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/chat_system")

# Fix for Heroku-style postgres:// URLs
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",  # Log SQL queries in development
    pool_size=int(os.getenv("DB_POOL_SIZE", "10")),  # Connection pool size
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),  # Max overflow connections
    pool_pre_ping=True,  # Verify connections before using them
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()

__all__ = ["Base", "engine", "SessionLocal"]