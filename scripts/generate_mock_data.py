#!/usr/bin/env python3
"""
Script to generate mock data for the wholesale agent.
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wholesale_agent.utils.migrations import migration_manager
from wholesale_agent.utils.mock_data import MockDataGenerator


def main():
    """Generate mock data for development and testing."""
    print("🔧 Initializing database...")
    
    # Initialize database
    migration_manager.init_db()
    
    # Run any pending migrations
    migration_manager.run_migrations()
    
    # Generate mock data
    generator = MockDataGenerator()
    generator.generate_all_data(
        categories_count=10,
        suppliers_count=15,
        products_per_category=30,
        movements_count=300
    )
    
    print("\n🎉 Setup complete! The wholesale agent is ready to use.")
    print("Run: python -m wholesale_agent.cli.main")


if __name__ == "__main__":
    main()