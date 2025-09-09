"""
Database migration utilities.
"""
import os
import json
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import text
from ..models import db_manager, Base


class MigrationManager:
    """Manages database migrations."""
    
    def __init__(self, migrations_dir: str = "migrations"):
        self.migrations_dir = migrations_dir
        self.migration_table = "schema_migrations"
        
    def ensure_migration_table(self):
        """Create migration tracking table if it doesn't exist."""
        with db_manager.get_session() as session:
            session.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {self.migration_table} (
                    id INTEGER PRIMARY KEY,
                    version VARCHAR(50) NOT NULL UNIQUE,
                    name VARCHAR(255) NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            session.commit()
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions."""
        self.ensure_migration_table()
        with db_manager.get_session() as session:
            result = session.execute(
                text(f"SELECT version FROM {self.migration_table} ORDER BY version")
            )
            return [row[0] for row in result.fetchall()]
    
    def get_pending_migrations(self) -> List[Dict[str, Any]]:
        """Get list of pending migrations."""
        applied = set(self.get_applied_migrations())
        pending = []
        
        migration_files = self._get_migration_files()
        for migration_file in migration_files:
            version = migration_file.split('_')[0]
            if version not in applied:
                pending.append({
                    'version': version,
                    'file': migration_file,
                    'path': os.path.join(self.migrations_dir, migration_file)
                })
        
        return sorted(pending, key=lambda x: x['version'])
    
    def _get_migration_files(self) -> List[str]:
        """Get all migration files from migrations directory."""
        if not os.path.exists(self.migrations_dir):
            return []
        
        files = []
        for filename in os.listdir(self.migrations_dir):
            if filename.endswith('.py') and filename != '__init__.py':
                files.append(filename)
        
        return sorted(files)
    
    def create_migration(self, name: str) -> str:
        """Create a new migration file."""
        os.makedirs(self.migrations_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version = f"{timestamp}_{name.lower().replace(' ', '_')}"
        filename = f"{version}.py"
        filepath = os.path.join(self.migrations_dir, filename)
        
        template = f'''"""
Migration: {name}
Created: {datetime.now().isoformat()}
"""
from sqlalchemy import text
from wholesale_agent.models import db_manager


def upgrade():
    """Apply migration."""
    with db_manager.get_session() as session:
        # Add your migration code here
        pass


def downgrade():
    """Rollback migration."""
    with db_manager.get_session() as session:
        # Add your rollback code here
        pass
'''
        
        with open(filepath, 'w') as f:
            f.write(template)
        
        return filename
    
    def run_migrations(self) -> bool:
        """Run all pending migrations."""
        pending = self.get_pending_migrations()
        
        if not pending:
            print("No pending migrations.")
            return True
        
        self.ensure_migration_table()
        
        for migration in pending:
            print(f"Applying migration: {migration['file']}")
            
            try:
                # Import and execute migration
                migration_module = self._import_migration(migration['path'])
                migration_module.upgrade()
                
                # Record migration as applied
                with db_manager.get_session() as session:
                    session.execute(text(f"""
                        INSERT INTO {self.migration_table} (version, name)
                        VALUES ('{migration['version']}', '{migration['file']}')
                    """))
                    session.commit()
                
                print(f"✓ Applied migration: {migration['file']}")
                
            except Exception as e:
                print(f"✗ Failed to apply migration {migration['file']}: {str(e)}")
                return False
        
        return True
    
    def _import_migration(self, filepath: str):
        """Dynamically import a migration file."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("migration", filepath)
        migration_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration_module)
        return migration_module
    
    def init_db(self):
        """Initialize database with all tables."""
        print("Initializing database...")
        db_manager.create_tables()
        
        # Mark initial migration as applied
        self.ensure_migration_table()
        with db_manager.get_session() as session:
            # Check if we already have the initial migration
            result = session.execute(
                text(f"SELECT COUNT(*) FROM {self.migration_table} WHERE version = '001_initial'")
            )
            count = result.fetchone()[0]
            
            if count == 0:
                session.execute(text(f"""
                    INSERT INTO {self.migration_table} (version, name)
                    VALUES ('001_initial', 'Initial database schema')
                """))
                session.commit()
        
        print("✓ Database initialized successfully.")


migration_manager = MigrationManager()