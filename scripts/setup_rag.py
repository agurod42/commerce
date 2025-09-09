#!/usr/bin/env python3
"""
Setup script for RAG (Retrieval-Augmented Generation) pipeline.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wholesale_agent.core.rag_pipeline import RAGPipeline
from wholesale_agent.utils.logger import setup_logger


def main():
    """Set up RAG pipeline with indexed data."""
    logger = setup_logger('rag_setup', 'INFO')
    
    print("🔍 Setting up RAG Pipeline for Wholesale Agent")
    print("=" * 50)
    
    try:
        # Initialize RAG pipeline
        print("📚 Initializing RAG pipeline...")
        pipeline = RAGPipeline()
        
        if not pipeline.enabled:
            print("❌ RAG pipeline is disabled")
            print("💡 Install dependencies with: pip install sentence-transformers faiss-cpu")
            return False
        
        # Index product data
        print("🏗️  Indexing product data...")
        pipeline.index_product_data()
        
        # Save index
        print("💾 Saving RAG index...")
        pipeline.save_index()
        
        # Test search
        print("🧪 Testing RAG search...")
        test_queries = [
            "wireless headphones",
            "low stock products", 
            "electronics category",
            "TechCorp supplier"
        ]
        
        for query in test_queries:
            results = pipeline.search_relevant_context(query, k=2)
            print(f"  Query: '{query}' -> {len(results)} results")
            
            for result in results[:1]:  # Show top result
                print(f"    📄 {result['content'][:80]}... (score: {result['relevance_score']:.3f})")
        
        print("\n✅ RAG pipeline setup completed successfully!")
        print("🚀 You can now enable RAG in your agent with enable_rag=True")
        
        return True
        
    except Exception as e:
        logger.error(f"RAG setup failed: {e}", exc_info=True)
        print(f"❌ RAG setup failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)