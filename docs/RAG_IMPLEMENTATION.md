# RAG (Retrieval-Augmented Generation) Implementation

## Overview

The Wholesale AI Agent now supports **RAG (Retrieval-Augmented Generation)** as an optional enhancement to provide more contextual and semantically relevant responses.

## Current Architecture vs RAG Enhancement

### Without RAG (Current Default)
```
User Query → Intent Analysis → Direct Database Query → LLM + Structured Data → Response
```

**Pros:**
- Fast and accurate for structured data
- Real-time inventory information
- Precise quantitative answers
- No additional setup required

**Cons:**
- Limited semantic understanding
- Struggles with fuzzy product descriptions
- Can't leverage historical knowledge
- No cross-product relationships

### With RAG Enhancement
```
User Query → Intent Analysis → Direct Database Query + Vector Search → LLM + Enhanced Context → Response
```

**Additional Benefits:**
- Semantic search across product descriptions
- Better handling of ambiguous queries
- Cross-product recommendations
- Historical context awareness
- Enhanced product discovery

## Installation

Install RAG dependencies:

```bash
pip install sentence-transformers faiss-cpu
# Or for GPU acceleration:
# pip install sentence-transformers faiss-gpu
```

## Setup

### 1. Index Your Data

```bash
# Set up RAG index with product data
python -m wholesale_agent.cli.main --setup-rag
```

This creates vector embeddings for:
- Product names and descriptions
- Category information
- Supplier details
- Cross-references and relationships

### 2. Enable RAG in Agent

```bash
# Start agent with RAG enabled
python -m wholesale_agent.cli.main --enable-rag
```

Or programmatically:
```python
from wholesale_agent.core.agent import WholesaleAgent

agent = WholesaleAgent(enable_rag=True)
```

## Usage Examples

### Traditional Query (Without RAG)
```
User: "USB cable stock"
System: → Searches products with name containing "USB cable"
Response: Found 2 USB cable products with current stock levels
```

### RAG-Enhanced Query
```
User: "charging accessories for phones"
System: → Semantic search finds related products:
         - USB-C cables
         - Wireless chargers  
         - Power banks
         - Lightning cables
Response: Found 8 phone charging accessories including USB-C cables (50 units), 
         wireless chargers (23 units), and power banks (31 units)
```

### Complex Semantic Queries
```
User: "products similar to wireless headphones but cheaper"
RAG Enhancement: Finds semantically similar products in audio category
                with lower price points (earbuds, wired headphones, etc.)
```

## Architecture Details

### Vector Embedding Pipeline

```python
class EmbeddingGenerator:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        # Lightweight, fast sentence transformer
        # 384-dimensional embeddings
        # Good balance of speed vs accuracy
```

### Vector Store (FAISS)

```python
class VectorStore:
    def __init__(self, dimension=384):
        # Inner product index for cosine similarity
        # Normalized embeddings for semantic search
        # Persistent storage with save/load
```

### Document Types Indexed

1. **Products**
   ```
   "Product: Wireless Bluetooth Headphones | SKU: ELE-1234-001 | 
    Category: Electronics | Supplier: TechCorp | Description: High-quality 
    wireless headphones with noise cancellation | Price: Wholesale $65.00, 
    Retail $99.99 | Stock: 100 units (IN_STOCK)"
   ```

2. **Categories**
   ```
   "Category: Electronics | Description: Electronic devices and accessories | 
    Contains 85 products"
   ```

3. **Suppliers**
   ```
   "Supplier: TechCorp Wholesale | Contact: orders@techcorp.com | 
    Payment Terms: Net 30 | Supplies 45 products"
   ```

## Configuration

### Environment Variables

```bash
# Enable RAG by default
ENABLE_RAG=true

# RAG-specific settings
RAG_MODEL=all-MiniLM-L6-v2
RAG_INDEX_PATH=data/rag_index
RAG_SEARCH_K=5  # Number of results to retrieve
```

### Embedding Models

Choose based on your needs:

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| `all-MiniLM-L6-v2` | 22MB | Fast | Good | Default, balanced |
| `all-mpnet-base-v2` | 420MB | Medium | Better | Higher accuracy needed |
| `multi-qa-MiniLM-L6-cos-v1` | 22MB | Fast | Good | Q&A focused |

## Performance Considerations

### Memory Usage
- **Base system**: ~50MB
- **With RAG**: +100-500MB (depending on model and index size)
- **Index storage**: ~1-5MB per 1000 products

### Response Time
- **Without RAG**: 200-500ms average
- **With RAG**: +50-200ms overhead for vector search
- **GPU acceleration**: Can reduce embedding time by 5-10x

### Optimization Tips

1. **Batch Processing**: Index updates in batches
2. **Caching**: Cache embeddings for frequently queried products
3. **Index Optimization**: Rebuild index periodically for better performance
4. **Selective Indexing**: Only index active products

## Integration Patterns

### Hybrid Search Strategy

```python
def enhanced_search(query: str):
    # 1. Traditional structured search
    structured_results = database_query(query)
    
    # 2. Semantic RAG search  
    semantic_results = rag_search(query)
    
    # 3. Combine and rank results
    return combine_results(structured_results, semantic_results)
```

### Contextual Enhancement

```python
def get_enhanced_context(query: str, traditional_context: dict):
    # Add semantic context
    rag_context = rag_pipeline.search_relevant_context(query)
    
    return {
        **traditional_context,
        'semantic_context': rag_context,
        'enhanced_insights': generate_insights(rag_context)
    }
```

## Maintenance

### Rebuilding Index

```bash
# Rebuild RAG index (run after significant data changes)
python -m wholesale_agent.core.rag_pipeline --rebuild
```

### Monitoring Index Health

```python
# Check index statistics
from wholesale_agent.core.rag_pipeline import RAGPipeline

pipeline = RAGPipeline()
pipeline.load_index()

print(f"Documents indexed: {pipeline.vector_store.index.ntotal}")
print(f"Index size: {pipeline.vector_store.dimension} dimensions")
```

### Automatic Reindexing

Set up periodic reindexing:

```bash
# Cron job to rebuild index daily
0 2 * * * cd /path/to/wholesale-agent && python -m wholesale_agent.core.rag_pipeline --rebuild
```

## Limitations and Trade-offs

### When RAG Helps
- ✅ Fuzzy product searches ("something like X")
- ✅ Cross-category recommendations  
- ✅ Semantic similarity queries
- ✅ Natural language product discovery
- ✅ Complex multi-attribute searches

### When Traditional DB is Better
- ✅ Exact inventory quantities
- ✅ Precise SKU lookups
- ✅ Real-time stock changes
- ✅ Structured data queries
- ✅ Financial calculations

### Current Limitations
- ❌ Requires additional memory and compute
- ❌ Index updates not real-time
- ❌ Setup complexity
- ❌ Dependency on external libraries
- ❌ Potential for semantic false positives

## Future Enhancements

### Planned Features
1. **Real-time indexing**: Automatic index updates on data changes
2. **Multi-modal RAG**: Include product images and documents
3. **Personalized embeddings**: User-specific search optimization
4. **A/B testing**: Compare RAG vs traditional responses
5. **Advanced ranking**: ML-based result scoring

### Possible Integrations
- **Product catalogs**: Index supplier catalogs and datasheets
- **Documentation**: Include product manuals and specifications
- **Historical data**: Learn from past queries and outcomes
- **Market intelligence**: External market data integration

## Troubleshooting

### Common Issues

**RAG not initializing**
```bash
pip install sentence-transformers faiss-cpu
python -m wholesale_agent.cli.main --setup-rag
```

**Index not found**
```bash
# Rebuild index
python -m wholesale_agent.core.rag_pipeline --rebuild
```

**Poor search results**
```bash
# Try different embedding model
export RAG_MODEL=all-mpnet-base-v2
python -m wholesale_agent.cli.main --setup-rag
```

**Memory issues**
```bash
# Use smaller model
export RAG_MODEL=all-MiniLM-L6-v2
# Or disable RAG for memory-constrained environments
python -m wholesale_agent.cli.main  # (without --enable-rag)
```

## Conclusion

RAG enhancement provides significant value for complex, semantic queries while maintaining the speed and accuracy of direct database queries for structured data. The hybrid approach gives you the best of both worlds - precise inventory management with intelligent product discovery.

Choose RAG when you need:
- Enhanced product discovery
- Semantic search capabilities  
- Better handling of natural language queries
- Cross-product recommendations

Stick with traditional queries for:
- Real-time inventory accuracy
- Exact numerical calculations
- Simple SKU/category lookups
- Memory-constrained environments