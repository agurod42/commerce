"""
Base database model and configuration.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime, Integer, create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

Base = declarative_base()
metadata = MetaData()


class BaseModel(Base):
    """Base model with common fields."""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class DatabaseManager:
    """Database connection and session management."""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv(
            'DATABASE_URL', 
            'sqlite:///wholesale_agent.db'
        )
        self.engine = create_engine(
            self.database_url,
            echo=os.getenv('DEBUG', 'false').lower() == 'true'
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get a database session."""
        return self.SessionLocal()
    
    def drop_tables(self):
        """Drop all database tables."""
        Base.metadata.drop_all(bind=self.engine)


db_manager = DatabaseManager()