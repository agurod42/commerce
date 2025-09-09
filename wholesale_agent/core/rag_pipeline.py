"""
RAG (Retrieval-Augmented Generation) pipeline for wholesale agent.
Useful for unstructured data like product descriptions, supplier docs, etc.
"""
import os
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
import numpy as np
from dataclasses import dataclass

try:
    from sentence_transformers import SentenceTransformer
    import faiss
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("Warning: sentence-transformers and faiss not installed. RAG features disabled.")

from ..models import db_manager, Product, Category, Supplier
from ..utils.logger import get_logger


@dataclass
class Document:
    """Document for RAG retrieval."""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None


class EmbeddingGenerator:
    """Generate embeddings for text documents."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if not EMBEDDINGS_AVAILABLE:
            raise ImportError("sentence-transformers not installed. Install with: pip install sentence-transformers faiss-cpu")
        
        self.model = SentenceTransformer(model_name)
        self.logger = get_logger(__name__)
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts."""
        try:
            embeddings = self.model.encode(texts, convert_to_tensor=False, show_progress_bar=True)
            return np.array(embeddings)
        except Exception as e:
            self.logger.error(f"Error generating embeddings: {e}")
            raise


class VectorStore:
    """Vector store using FAISS for similarity search."""
    
    def __init__(self, dimension: int = 384):
        if not EMBEDDINGS_AVAILABLE:
            raise ImportError("faiss not installed. Install with: pip install faiss-cpu")
        
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        self.documents = []
        self.logger = get_logger(__name__)
    
    def add_documents(self, documents: List[Document]):
        """Add documents to the vector store."""
        if not documents:
            return
        
        # Extract embeddings
        embeddings = np.array([doc.embedding for doc in documents if doc.embedding is not None])
        
        if len(embeddings) == 0:
            self.logger.warning("No embeddings found in documents")
            return
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Add to index
        self.index.add(embeddings.astype('float32'))
        self.documents.extend(documents)
        
        self.logger.info(f"Added {len(embeddings)} documents to vector store")
    
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[tuple]:
        """Search for similar documents."""
        if self.index.ntotal == 0:
            return []
        
        # Normalize query embedding
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.index.search(query_embedding, k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.documents):
                results.append((self.documents[idx], float(score)))
        
        return results
    
    def save(self, filepath: str):
        """Save vector store to disk."""
        index_path = f"{filepath}.index"
        docs_path = f"{filepath}.docs"
        
        # Save FAISS index
        faiss.write_index(self.index, index_path)
        
        # Save documents
        docs_data = [
            {
                'id': doc.id,
                'content': doc.content,
                'metadata': doc.metadata
            }
            for doc in self.documents
        ]
        
        with open(docs_path, 'w') as f:
            json.dump(docs_data, f, indent=2)
        
        self.logger.info(f"Vector store saved to {filepath}")
    
    def load(self, filepath: str):
        """Load vector store from disk."""
        index_path = f"{filepath}.index"
        docs_path = f"{filepath}.docs"
        
        if not (Path(index_path).exists() and Path(docs_path).exists()):
            raise FileNotFoundError(f"Vector store files not found at {filepath}")
        
        # Load FAISS index
        self.index = faiss.read_index(index_path)
        
        # Load documents
        with open(docs_path, 'r') as f:
            docs_data = json.load(f)
        
        self.documents = [
            Document(
                id=doc['id'],
                content=doc['content'],
                metadata=doc['metadata']
            )
            for doc in docs_data
        ]
        
        self.logger.info(f"Vector store loaded from {filepath}")


class RAGPipeline:
    """Complete RAG pipeline for wholesale agent."""
    
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        if not EMBEDDINGS_AVAILABLE:
            self.logger = get_logger(__name__)
            self.logger.warning("RAG pipeline disabled - missing dependencies")
            self.enabled = False
            return
        
        self.enabled = True
        self.embedding_generator = EmbeddingGenerator(embedding_model)
        self.vector_store = VectorStore()
        self.logger = get_logger(__name__)
    
    def index_product_data(self):
        """Index product data for RAG retrieval."""
        if not self.enabled:
            return
        
        self.logger.info("Indexing product data for RAG...")
        
        documents = []
        
        with db_manager.get_session() as session:
            # Index product descriptions and details
            products = session.query(Product).filter(Product.is_active == True).all()
            
            for product in products:
                # Create rich text content for each product
                content_parts = [
                    f"Product: {product.name}",
                    f"SKU: {product.sku}",
                    f"Category: {product.category.name}",
                    f"Supplier: {product.supplier.name}",
                ]
                
                if product.description:
                    content_parts.append(f"Description: {product.description}")
                
                content_parts.extend([
                    f"Price: Wholesale ${product.wholesale_price:.2f}, Retail ${product.retail_price:.2f}",
                    f"Stock: {product.current_stock} units ({product.stock_status})",
                    f"Weight: {product.weight}kg" if product.weight else "",
                    f"Dimensions: {product.dimensions}" if product.dimensions else "",
                ])
                
                content = " | ".join([part for part in content_parts if part])
                
                doc = Document(
                    id=f"product_{product.id}",
                    content=content,
                    metadata={
                        'type': 'product',
                        'product_id': product.id,
                        'sku': product.sku,
                        'name': product.name,
                        'category': product.category.name,
                        'supplier': product.supplier.name,
                        'stock_status': product.stock_status
                    }
                )
                documents.append(doc)
            
            # Index category information
            categories = session.query(Category).all()
            for category in categories:
                content = f"Category: {category.name}"
                if category.description:
                    content += f" | Description: {category.description}"
                
                # Add product count and examples
                product_count = len([p for p in category.products if p.is_active])
                content += f" | Contains {product_count} products"
                
                doc = Document(
                    id=f"category_{category.id}",
                    content=content,
                    metadata={
                        'type': 'category',
                        'category_id': category.id,
                        'name': category.name,
                        'product_count': product_count
                    }
                )
                documents.append(doc)
            
            # Index supplier information
            suppliers = session.query(Supplier).filter(Supplier.is_active == True).all()
            for supplier in suppliers:
                content_parts = [
                    f"Supplier: {supplier.name}",
                    f"Contact: {supplier.contact_email}" if supplier.contact_email else "",
                    f"Phone: {supplier.contact_phone}" if supplier.contact_phone else "",
                    f"Payment Terms: {supplier.payment_terms}" if supplier.payment_terms else "",
                ]
                
                content = " | ".join([part for part in content_parts if part])
                
                product_count = len([p for p in supplier.products if p.is_active])
                content += f" | Supplies {product_count} products"
                
                doc = Document(
                    id=f"supplier_{supplier.id}",
                    content=content,
                    metadata={
                        'type': 'supplier',
                        'supplier_id': supplier.id,
                        'name': supplier.name,
                        'product_count': product_count
                    }
                )
                documents.append(doc)
        
        if documents:
            # Generate embeddings
            texts = [doc.content for doc in documents]
            embeddings = self.embedding_generator.generate_embeddings(texts)
            
            # Add embeddings to documents
            for doc, embedding in zip(documents, embeddings):
                doc.embedding = embedding
            
            # Add to vector store
            self.vector_store.add_documents(documents)
            
            self.logger.info(f"Indexed {len(documents)} documents for RAG")
    
    def search_relevant_context(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant context using RAG."""
        if not self.enabled or self.vector_store.index.ntotal == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_embeddings([query])[0]
        
        # Search vector store
        results = self.vector_store.search(query_embedding, k)
        
        # Format results
        context_docs = []
        for doc, score in results:
            context_docs.append({
                'content': doc.content,
                'metadata': doc.metadata,
                'relevance_score': score,
                'type': doc.metadata.get('type', 'unknown')
            })
        
        return context_docs
    
    def get_rag_enhanced_context(self, query: str, traditional_context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance traditional context with RAG-retrieved information."""
        if not self.enabled:
            return traditional_context
        
        # Get RAG context
        rag_context = self.search_relevant_context(query, k=3)
        
        # Merge with traditional context
        enhanced_context = traditional_context.copy()
        if rag_context:
            enhanced_context['rag_context'] = {
                'relevant_documents': rag_context,
                'note': 'Additional context retrieved using semantic search'
            }
        
        return enhanced_context
    
    def save_index(self, filepath: str = "data/rag_index"):
        """Save RAG index to disk."""
        if not self.enabled:
            return
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.vector_store.save(filepath)
    
    def load_index(self, filepath: str = "data/rag_index"):
        """Load RAG index from disk."""
        if not self.enabled:
            return
        
        try:
            self.vector_store.load(filepath)
            self.logger.info("RAG index loaded successfully")
        except FileNotFoundError:
            self.logger.warning("RAG index not found, will need to rebuild")
    
    def rebuild_index(self):
        """Rebuild the entire RAG index."""
        if not self.enabled:
            return
        
        self.vector_store = VectorStore()  # Reset
        self.index_product_data()
        self.save_index()


# Integration with main agent
def enhance_agent_with_rag():
    """Example of how to integrate RAG with the main agent."""
    
    # This would be added to wholesale_agent/core/agent.py
    """
    class WholesaleAgent:
        def __init__(self, llm_client=None, enable_rag=False):
            # ... existing initialization ...
            
            self.rag_pipeline = None
            if enable_rag:
                try:
                    self.rag_pipeline = RAGPipeline()
                    self.rag_pipeline.load_index()  # Load existing index
                except Exception as e:
                    self.logger.warning(f"RAG initialization failed: {e}")
        
        def _get_context_data(self, query_intent):
            # ... existing context gathering ...
            
            # Enhance with RAG if available
            if self.rag_pipeline and self.rag_pipeline.enabled:
                context = self.rag_pipeline.get_rag_enhanced_context(
                    query_intent.get('original_query', ''), 
                    context
                )
            
            return context
    """


def main():
    """CLI for RAG pipeline management."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Manage RAG pipeline for wholesale agent')
    parser.add_argument('--rebuild', action='store_true', help='Rebuild RAG index')
    parser.add_argument('--search', type=str, help='Test search query')
    
    args = parser.parse_args()
    
    pipeline = RAGPipeline()
    
    if not pipeline.enabled:
        print("RAG pipeline is disabled. Install dependencies with:")
        print("pip install sentence-transformers faiss-cpu")
        return
    
    if args.rebuild:
        print("Rebuilding RAG index...")
        pipeline.rebuild_index()
        print("RAG index rebuilt successfully")
    
    if args.search:
        pipeline.load_index()
        results = pipeline.search_relevant_context(args.search)
        
        print(f"\nSearch results for: '{args.search}'")
        print("=" * 50)
        
        for i, result in enumerate(results, 1):
            print(f"{i}. [{result['type']}] Score: {result['relevance_score']:.3f}")
            print(f"   {result['content'][:200]}...")
            print()


if __name__ == "__main__":
    main()