"""
Migration: Initial database schema
Created: 2025-01-15T00:00:00
"""
from sqlalchemy import text
from wholesale_agent.models import db_manager


def upgrade():
    """Apply migration - create initial schema."""
    # This migration is handled by the ORM create_tables method
    # It's here for tracking purposes
    pass


def downgrade():
    """Rollback migration - drop all tables."""
    with db_manager.get_session() as session:
        # Drop all tables
        session.execute(text("DROP TABLE IF EXISTS inventory_movements"))
        session.execute(text("DROP TABLE IF EXISTS products"))
        session.execute(text("DROP TABLE IF EXISTS categories"))
        session.execute(text("DROP TABLE IF EXISTS suppliers"))
        session.commit()