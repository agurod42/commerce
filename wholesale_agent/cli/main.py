#!/usr/bin/env python3
"""
Main CLI entry point for wholesale agent.
"""
import sys
import argparse
import os
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from wholesale_agent.cli.chat import ChatInterface
from wholesale_agent.utils.config import Config
from wholesale_agent.utils.migrations import migration_manager
from wholesale_agent.utils.mock_data import MockDataGenerator


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Wholesale AI Agent - Your AI assistant for wholesale business operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Start interactive chat
  %(prog)s --setup            # Initialize database and generate mock data
  %(prog)s --migrate          # Run database migrations
  %(prog)s --query "stock"    # Run single query and exit
  %(prog)s --config-check     # Check configuration
        """
    )
    
    parser.add_argument(
        '--setup',
        action='store_true',
        help='Initialize database and generate mock data'
    )
    
    parser.add_argument(
        '--migrate',
        action='store_true',
        help='Run database migrations'
    )
    
    parser.add_argument(
        '--query', '-q',
        type=str,
        help='Run a single query and exit'
    )
    
    parser.add_argument(
        '--config-check',
        action='store_true',
        help='Check system configuration'
    )
    
    parser.add_argument(
        '--generate-data',
        action='store_true',
        help='Generate mock data only'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--enable-rag',
        action='store_true',
        help='Enable RAG (Retrieval-Augmented Generation) pipeline'
    )
    
    parser.add_argument(
        '--setup-rag',
        action='store_true',
        help='Set up and index data for RAG pipeline'
    )
    
    return parser


def setup_database():
    """Initialize database with schema and mock data."""
    print("🔧 Setting up database...")
    
    # Initialize database
    migration_manager.init_db()
    
    # Run migrations
    print("📦 Running migrations...")
    success = migration_manager.run_migrations()
    
    if not success:
        print("❌ Migration failed. Please check the logs.")
        return False
    
    # Generate mock data
    print("🎲 Generating mock data...")
    generator = MockDataGenerator()
    generator.generate_all_data()
    
    print("✅ Database setup completed successfully!")
    return True


def run_migrations():
    """Run database migrations."""
    print("📦 Running database migrations...")
    success = migration_manager.run_migrations()
    
    if success:
        print("✅ Migrations completed successfully!")
    else:
        print("❌ Migration failed. Please check the logs.")
        return False
    
    return True


def generate_mock_data():
    """Generate mock data."""
    print("🎲 Generating mock data...")
    
    try:
        generator = MockDataGenerator()
        generator.generate_all_data()
        print("✅ Mock data generated successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to generate mock data: {str(e)}")
        return False


def run_single_query(query: str, config: Config):
    """Run a single query and exit."""
    from wholesale_agent.core import WholesaleAgent
    
    print(f"🔍 Processing query: {query}")
    print("─" * 50)
    
    try:
        agent = WholesaleAgent()
        response = agent.process_query(query)
        print(response)
        return True
    except Exception as e:
        print(f"❌ Error processing query: {str(e)}")
        return False


def check_configuration(config: Config):
    """Check system configuration."""
    print("⚙️  System Configuration Check")
    print("=" * 40)
    
    # Database connectivity
    print("🗄️  Database:")
    try:
        from wholesale_agent.models import db_manager
        with db_manager.get_session() as session:
            session.execute("SELECT 1")
        print("  ✅ Database connection: OK")
    except Exception as e:
        print(f"  ❌ Database connection: FAILED ({str(e)})")
    
    # LLM configuration
    print("\\n🤖 AI Model:")
    try:
        from wholesale_agent.core import LLMClient
        llm_client = LLMClient()
        model_info = llm_client.get_model_info()
        print(f"  Provider: {model_info.get('provider', 'Unknown')}")
        print(f"  Model: {model_info.get('model', 'Unknown')}")
        print(f"  Status: {'✅ Available' if model_info.get('available') else '❌ Unavailable'}")
    except Exception as e:
        print(f"  ❌ LLM configuration: FAILED ({str(e)})")
    
    # Environment variables
    print("\\n🌍 Environment:")
    env_vars = [
        'LLM_PROVIDER',
        'LLM_API_KEY',
        'LLM_MODEL',
        'DATABASE_URL',
        'DEBUG'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'key' in var.lower() or 'token' in var.lower():
                value = value[:8] + "..." if len(value) > 8 else "***"
            print(f"  {var}: {value}")
        else:
            print(f"  {var}: Not set")
    
    print("\\n🔍 Quick Test:")
    try:
        from wholesale_agent.core import WholesaleAgent
        agent = WholesaleAgent()
        response = agent.process_query("system status")
        print("  ✅ Agent query test: PASSED")
    except Exception as e:
        print(f"  ❌ Agent query test: FAILED ({str(e)})")
    
    print("\\n" + "=" * 40)
    print("Configuration check completed!")


def setup_rag():
    """Set up RAG pipeline."""
    try:
        from ..core.rag_pipeline import RAGPipeline
        
        print("🔍 Setting up RAG Pipeline...")
        pipeline = RAGPipeline()
        
        if not pipeline.enabled:
            print("❌ RAG dependencies not installed")
            print("💡 Install with: pip install sentence-transformers faiss-cpu")
            return False
        
        pipeline.index_product_data()
        pipeline.save_index()
        
        print("✅ RAG pipeline setup completed!")
        return True
        
    except Exception as e:
        print(f"❌ RAG setup failed: {e}")
        return False


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Load configuration
    config = Config(
        config_file=args.config,
        debug=args.debug
    )
    
    # Handle specific commands
    if args.setup:
        success = setup_database()
        sys.exit(0 if success else 1)
    
    elif args.migrate:
        success = run_migrations()
        sys.exit(0 if success else 1)
    
    elif args.generate_data:
        success = generate_mock_data()
        sys.exit(0 if success else 1)
    
    elif args.config_check:
        check_configuration(config)
        sys.exit(0)
    
    elif args.setup_rag:
        success = setup_rag()
        sys.exit(0 if success else 1)
    
    elif args.query:
        success = run_single_query(args.query, config)
        sys.exit(0 if success else 1)
    
    else:
        # Start interactive chat
        try:
            chat = ChatInterface(config, enable_rag=args.enable_rag)
            chat.start()
        except KeyboardInterrupt:
            print("\\n👋 Goodbye!")
        except Exception as e:
            print(f"❌ Fatal error: {str(e)}")
            sys.exit(1)


if __name__ == "__main__":
    main()