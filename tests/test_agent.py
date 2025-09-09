"""
Tests for the main AI agent functionality.
"""
import pytest
from unittest.mock import patch, MagicMock

from wholesale_agent.core.agent import WholesaleAgent


@pytest.mark.unit
class TestWholesaleAgent:
    """Test WholesaleAgent functionality."""
    
    @pytest.fixture
    def agent(self, mock_llm_client):
        """Create agent instance with mocked LLM client."""
        return WholesaleAgent()
    
    def test_agent_initialization(self, agent):
        """Test agent initialization."""
        assert agent.llm_client is not None
        assert agent.query_processor is not None
        assert agent.system_prompt is not None
        assert "wholesale business" in agent.system_prompt.lower()
    
    def test_process_query_basic(self, agent):
        """Test basic query processing."""
        with patch.object(agent.query_processor, 'analyze_intent') as mock_analyze:
            with patch.object(agent, '_get_context_data') as mock_context:
                with patch.object(agent, '_generate_response') as mock_generate:
                    
                    mock_analyze.return_value = {'type': 'general', 'entities': {}, 'keywords': []}
                    mock_context.return_value = {'test': 'data'}
                    mock_generate.return_value = "Test response"
                    
                    result = agent.process_query("test query")
                    
                    assert result == "Test response"
                    mock_analyze.assert_called_once_with("test query")
                    mock_context.assert_called_once()
                    mock_generate.assert_called_once()
    
    def test_process_query_with_error(self, agent):
        """Test query processing with error handling."""
        with patch.object(agent.query_processor, 'analyze_intent') as mock_analyze:
            mock_analyze.side_effect = Exception("Test error")
            
            result = agent.process_query("test query")
            
            assert "error processing your request" in result.lower()
            assert "Test error" in result
    
    def test_get_inventory_context(self, agent):
        """Test getting inventory context."""
        with patch('wholesale_agent.core.agent.db_manager.get_session') as mock_session:
            mock_session.return_value.__enter__.return_value = MagicMock()
            session = mock_session.return_value.__enter__.return_value
            
            # Mock product query for specific product
            mock_product = MagicMock()
            mock_product.id = 1
            mock_product.sku = "TEST-001"
            mock_product.name = "Test Product"
            mock_product.current_stock = 50
            mock_product.minimum_stock = 10
            mock_product.stock_status = "IN_STOCK"
            mock_product.category.name = "Electronics"
            mock_product.supplier.name = "TechCorp"
            mock_product.wholesale_price = 25.0
            
            session.query.return_value.filter.return_value.limit.return_value.all.return_value = [mock_product]
            
            # Mock low stock products
            session.query.return_value.filter.return_value.limit.return_value.all.return_value = []
            
            # Mock out of stock count
            session.query.return_value.filter.return_value.count.return_value = 5
            
            query_intent = {
                'type': 'inventory_query',
                'product_name': 'test product'
            }
            
            context = agent._get_context_data(query_intent)
            
            assert 'matching_products' in context
            assert len(context['matching_products']) == 1
            assert context['matching_products'][0]['name'] == "Test Product"
            assert 'out_of_stock_count' in context
    
    def test_get_product_context(self, agent):
        """Test getting product search context."""
        with patch('wholesale_agent.core.agent.db_manager.get_session') as mock_session:
            mock_session.return_value.__enter__.return_value = MagicMock()
            session = mock_session.return_value.__enter__.return_value
            
            # Mock search results
            mock_products = []
            for i in range(3):
                mock_product = MagicMock()
                mock_product.id = i + 1
                mock_product.sku = f"TEST-{i+1:03d}"
                mock_product.name = f"Test Product {i+1}"
                mock_product.description = f"Description for product {i+1}"
                mock_product.current_stock = 50 + i * 10
                mock_product.wholesale_price = 20.0 + i * 5
                mock_product.retail_price = 35.0 + i * 8
                mock_product.category.name = "Electronics"
                mock_product.supplier.name = "TechCorp"
                mock_product.is_active = True
                mock_products.append(mock_product)
            
            session.query.return_value.filter.return_value.limit.return_value.all.return_value = mock_products
            
            query_intent = {
                'type': 'product_search',
                'search_term': 'wireless headphones'
            }
            
            context = agent._get_context_data(query_intent)
            
            assert 'search_results' in context
            assert len(context['search_results']) == 3
            assert context['search_results'][0]['name'] == "Test Product 1"
    
    def test_get_analytics_context(self, agent):
        """Test getting analytics context."""
        with patch('wholesale_agent.core.agent.db_manager.get_session') as mock_session:
            mock_session.return_value.__enter__.return_value = MagicMock()
            session = mock_session.return_value.__enter__.return_value
            
            # Mock total products and inventory value
            session.query.return_value.filter.return_value.count.return_value = 150
            session.query.return_value.filter.return_value.scalar.return_value = 75000.0
            
            # Mock top categories
            mock_categories = []
            for i, cat_name in enumerate(['Electronics', 'Clothing', 'Home & Garden']):
                mock_cat = MagicMock()
                mock_cat.name = cat_name
                mock_cat.product_count = 50 - i * 10
                mock_cat.category_value = 25000.0 - i * 5000
                mock_categories.append(mock_cat)
            
            session.query.return_value.join.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = mock_categories
            
            # Mock recent movements
            mock_movements = []
            for i in range(5):
                mock_movement = MagicMock()
                mock_movement.id = i + 1
                mock_movement.product.name = f"Product {i+1}"
                mock_movement.product.sku = f"SKU-{i+1:03d}"
                mock_movement.movement_type = "OUTBOUND" if i % 2 == 0 else "INBOUND"
                mock_movement.quantity = -10 if i % 2 == 0 else 20
                mock_movement.created_at.isoformat.return_value = f"2024-01-{i+1:02d}T10:00:00"
                mock_movement.reference_number = f"REF-{i+1:03d}"
                mock_movements.append(mock_movement)
            
            session.query.return_value.order_by.return_value.limit.return_value.all.return_value = mock_movements
            
            query_intent = {'type': 'analytics'}
            
            context = agent._get_context_data(query_intent)
            
            assert context['total_products'] == 150
            assert context['total_inventory_value'] == 75000.0
            assert len(context['top_categories']) == 3
            assert len(context['recent_movements']) == 5
    
    def test_generate_response_with_llm(self, agent):
        """Test response generation using LLM."""
        with patch.object(agent.llm_client, 'generate_response') as mock_llm:
            mock_llm.return_value = "AI generated response"
            
            query = "How much stock do we have?"
            context_data = {'test': 'data'}
            query_intent = {'type': 'inventory_query'}
            
            response = agent._generate_response(query, context_data, query_intent)
            
            assert response == "AI generated response"
            mock_llm.assert_called_once()
            
            # Check that the prompt includes the query and context
            call_args = mock_llm.call_args
            prompt = call_args[1]['prompt']
            assert query in prompt
            assert 'test' in prompt
    
    def test_generate_response_with_llm_error(self, agent):
        """Test response generation when LLM fails."""
        with patch.object(agent.llm_client, 'generate_response') as mock_llm:
            with patch.object(agent, '_generate_fallback_response') as mock_fallback:
                mock_llm.side_effect = Exception("LLM error")
                mock_fallback.return_value = "Fallback response"
                
                query = "test query"
                context_data = {}
                query_intent = {'type': 'general'}
                
                response = agent._generate_response(query, context_data, query_intent)
                
                assert response == "Fallback response"
                mock_fallback.assert_called_once_with(query, context_data, query_intent)
    
    def test_fallback_inventory_response(self, agent):
        """Test fallback response for inventory queries."""
        context_data = {
            'matching_products': [
                {
                    'name': 'Test Product',
                    'sku': 'TEST-001',
                    'current_stock': 50,
                    'stock_status': 'IN_STOCK'
                }
            ],
            'low_stock_products': [
                {
                    'name': 'Low Stock Item',
                    'current_stock': 5,
                    'minimum_stock': 20
                }
            ]
        }
        
        query_intent = {'type': 'inventory_query'}
        
        response = agent._handle_inventory_fallback(context_data)
        
        assert "Found 1 matching products" in response
        assert "Test Product" in response
        assert "1 products are running low" in response
        assert "Low Stock Item" in response
    
    def test_fallback_product_search_response(self, agent):
        """Test fallback response for product searches."""
        context_data = {
            'search_results': [
                {
                    'name': 'Product 1',
                    'sku': 'PRD-001',
                    'wholesale_price': 25.0,
                    'current_stock': 100
                },
                {
                    'name': 'Product 2',
                    'sku': 'PRD-002',
                    'wholesale_price': 15.0,
                    'current_stock': 50
                }
            ]
        }
        
        response = agent._handle_product_search_fallback(context_data)
        
        assert "Found 2 matching products" in response
        assert "Product 1" in response
        assert "Product 2" in response
        assert "$25.00" in response
        assert "$15.00" in response
    
    def test_fallback_analytics_response(self, agent):
        """Test fallback response for analytics queries."""
        context_data = {
            'total_products': 150,
            'total_inventory_value': 75000.0,
            'top_categories': [
                {'name': 'Electronics', 'product_count': 50, 'inventory_value': 30000.0},
                {'name': 'Clothing', 'product_count': 40, 'inventory_value': 25000.0}
            ]
        }
        
        response = agent._handle_analytics_fallback(context_data)
        
        assert "Total Products: 150" in response
        assert "$75,000.00" in response
        assert "Electronics: 50 products" in response
        assert "Clothing: 40 products" in response
    
    def test_format_context_for_llm(self, agent):
        """Test formatting context data for LLM."""
        context_data = {
            'simple_value': 'test',
            'numeric_value': 123,
            'list_data': [{'item': 1}, {'item': 2}],
            'dict_data': {'key': 'value'}
        }
        
        formatted = agent._format_context_for_llm(context_data)
        
        assert 'simple_value: test' in formatted
        assert 'numeric_value: 123' in formatted
        assert 'list_data:' in formatted
        assert 'dict_data:' in formatted
        # Should contain JSON formatting for complex data
        assert '"item": 1' in formatted
        assert '"key": "value"' in formatted


@pytest.mark.integration
class TestWholesaleAgentIntegration:
    """Integration tests for the wholesale agent."""
    
    @pytest.fixture
    def agent(self, mock_llm_client):
        """Create agent for integration testing."""
        return WholesaleAgent()
    
    def test_end_to_end_inventory_query(self, agent, sample_data):
        """Test complete inventory query flow."""
        # This would require setting up the database properly
        # For now, we'll mock the database calls
        with patch('wholesale_agent.core.agent.db_manager.get_session'):
            query = "How much stock of wireless headphones do we have?"
            
            # This should not raise an exception and should return some response
            response = agent.process_query(query)
            
            assert isinstance(response, str)
            assert len(response) > 0
    
    def test_end_to_end_product_search(self, agent):
        """Test complete product search flow."""
        with patch('wholesale_agent.core.agent.db_manager.get_session'):
            query = "Find USB cables"
            
            response = agent.process_query(query)
            
            assert isinstance(response, str)
            assert len(response) > 0
    
    def test_end_to_end_analytics_query(self, agent):
        """Test complete analytics query flow."""
        with patch('wholesale_agent.core.agent.db_manager.get_session'):
            query = "Show me business analytics"
            
            response = agent.process_query(query)
            
            assert isinstance(response, str)
            assert len(response) > 0