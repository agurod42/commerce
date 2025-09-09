"""
Tests for query processor functionality.
"""
import pytest

from wholesale_agent.core.query_processor import QueryProcessor


@pytest.mark.unit
class TestQueryProcessor:
    """Test QueryProcessor functionality."""
    
    @pytest.fixture
    def processor(self):
        """Create query processor instance."""
        return QueryProcessor()
    
    def test_inventory_query_classification(self, processor):
        """Test classification of inventory queries."""
        test_cases = [
            ("How much stock do we have?", "inventory_query"),
            ("What is the current stock level?", "inventory_query"),
            ("How many USB cables are in stock?", "inventory_query"),
            ("Show me low stock products", "inventory_query"),
            ("Which products are out of stock?", "inventory_query"),
        ]
        
        for query, expected_intent in test_cases:
            result = processor.analyze_intent(query)
            assert result['type'] == expected_intent, f"Failed for query: {query}"
    
    def test_product_search_classification(self, processor):
        """Test classification of product search queries."""
        test_cases = [
            ("Find wireless headphones", "product_search"),
            ("Search for USB cables", "product_search"),
            ("Show me products in electronics category", "product_search"),
            ("Look for bluetooth speakers", "product_search"),
            ("What products do we have?", "product_search"),
        ]
        
        for query, expected_intent in test_cases:
            result = processor.analyze_intent(query)
            assert result['type'] == expected_intent, f"Failed for query: {query}"
    
    def test_analytics_query_classification(self, processor):
        """Test classification of analytics queries."""
        test_cases = [
            ("Show me top selling products", "analytics"),
            ("What are our total sales?", "analytics"),
            ("Revenue report for last month", "analytics"),
            ("Analytics on product performance", "analytics"),
            ("Show statistics for electronics", "analytics"),
        ]
        
        for query, expected_intent in test_cases:
            result = processor.analyze_intent(query)
            assert result['type'] == expected_intent, f"Failed for query: {query}"
    
    def test_supplier_query_classification(self, processor):
        """Test classification of supplier queries."""
        test_cases = [
            ("Who supplies wireless headphones?", "supplier_query"),
            ("Show me all suppliers", "supplier_query"),
            ("Contact information for TechCorp", "supplier_query"),
            ("Which vendor provides USB cables?", "supplier_query"),
        ]
        
        for query, expected_intent in test_cases:
            result = processor.analyze_intent(query)
            assert result['type'] == expected_intent, f"Failed for query: {query}"
    
    def test_price_query_classification(self, processor):
        """Test classification of price queries."""
        test_cases = [
            ("What is the price of wireless headphones?", "price_query"),
            ("How much does USB cable cost?", "price_query"),
            ("Show me wholesale prices", "price_query"),
            ("What are the retail prices?", "price_query"),
        ]
        
        for query, expected_intent in test_cases:
            result = processor.analyze_intent(query)
            assert result['type'] == expected_intent, f"Failed for query: {query}"
    
    def test_general_query_classification(self, processor):
        """Test classification of general queries."""
        test_cases = [
            ("Hello", "general"),
            ("Help me", "general"), 
            ("What can you do?", "general"),
            ("Random text that doesn't match patterns", "general"),
        ]
        
        for query, expected_intent in test_cases:
            result = processor.analyze_intent(query)
            assert result['type'] == expected_intent, f"Failed for query: {query}"
    
    def test_entity_extraction_product_name(self, processor):
        """Test extraction of product names."""
        test_cases = [
            ("How much stock of wireless headphones do we have?", "wireless headphones"),
            ("Find USB cables in inventory", "USB cables"),
            ("Stock level for \"Bluetooth Speaker\"", "Bluetooth Speaker"),
            ("Search for 'Gaming Mouse'", "Gaming Mouse"),
        ]
        
        for query, expected_product in test_cases:
            result = processor.analyze_intent(query)
            entities = result.get('entities', {})
            
            # Check if product name or search term was extracted
            extracted = entities.get('product_name') or entities.get('search_term')
            assert extracted is not None, f"No product extracted from: {query}"
            assert expected_product.lower() in extracted.lower(), f"Expected '{expected_product}' in '{extracted}'"
    
    def test_entity_extraction_sku(self, processor):
        """Test extraction of SKU codes."""
        test_cases = [
            ("Stock for ELE-1234-001", "ELE-1234-001"),
            ("Find product with sku: TEC-5678-999", "TEC-5678-999"),
            ("Show me part ABC-1111-222", "ABC-1111-222"),
        ]
        
        for query, expected_sku in test_cases:
            result = processor.analyze_intent(query)
            entities = result.get('entities', {})
            
            assert 'sku' in entities, f"No SKU extracted from: {query}"
            assert entities['sku'] == expected_sku
    
    def test_entity_extraction_category(self, processor):
        """Test extraction of categories."""
        test_cases = [
            ("Products in Electronics category", "Electronics"),
            ("Show me items from Home & Garden category", "Home & Garden"),
            ("Category: Clothing products", "Clothing"),
        ]
        
        for query, expected_category in test_cases:
            result = processor.analyze_intent(query)
            entities = result.get('entities', {})
            
            assert 'category' in entities, f"No category extracted from: {query}"
            assert expected_category.lower() in entities['category'].lower()
    
    def test_entity_extraction_supplier(self, processor):
        """Test extraction of suppliers."""
        test_cases = [
            ("Products from TechCorp supplier", "TechCorp"),
            ("Items supplied by Global Supply Company", "Global Supply Company"),
            ("Show me supplier: Fashion Plus items", "Fashion Plus"),
        ]
        
        for query, expected_supplier in test_cases:
            result = processor.analyze_intent(query)
            entities = result.get('entities', {})
            
            assert 'supplier' in entities, f"No supplier extracted from: {query}"
            assert expected_supplier.lower() in entities['supplier'].lower()
    
    def test_keyword_extraction(self, processor):
        """Test extraction of relevant keywords."""
        query = "Show me low stock wireless headphones from electronics category"
        result = processor.analyze_intent(query)
        
        keywords = result.get('keywords', [])
        expected_keywords = ['stock', 'wireless', 'headphones', 'electronics', 'category']
        
        for keyword in expected_keywords:
            assert keyword in keywords, f"Missing keyword '{keyword}' in {keywords}"
    
    def test_query_suggestions(self, processor):
        """Test query suggestions functionality."""
        partial_query = "stock"
        suggestions = processor.get_query_suggestions(partial_query)
        
        assert len(suggestions) > 0
        assert all("stock" in suggestion.lower() for suggestion in suggestions)
        
        # Test with short query
        short_suggestions = processor.get_query_suggestions("ab")
        assert len(short_suggestions) == 0
    
    def test_query_validation(self, processor):
        """Test query validation."""
        # Valid queries
        valid_queries = [
            "How much stock do we have?",
            "Find wireless headphones",
            "Show me suppliers",
        ]
        
        for query in valid_queries:
            result = processor.validate_query(query)
            assert result['valid'] is True, f"Query should be valid: {query}"
        
        # Invalid queries
        invalid_queries = [
            "",
            "  ",
            "ab",  # Too short
            "123 + 456",  # Only math
            "!@#$%",  # Only special characters
        ]
        
        for query in invalid_queries:
            result = processor.validate_query(query)
            assert result['valid'] is False, f"Query should be invalid: {query}"
            assert 'reason' in result
    
    def test_complex_query_analysis(self, processor):
        """Test analysis of complex queries."""
        complex_query = "Show me low stock wireless headphones from TechCorp in Electronics category under $50"
        result = processor.analyze_intent(complex_query)
        
        assert result['type'] == 'inventory_query'
        
        entities = result['entities']
        keywords = result['keywords']
        
        # Should extract multiple entities
        assert 'search_term' in entities or 'product_name' in entities
        assert 'supplier' in entities
        assert 'category' in entities
        
        # Should have relevant keywords
        expected_keywords = ['stock', 'wireless', 'headphones', 'electronics']
        for keyword in expected_keywords:
            assert keyword in keywords