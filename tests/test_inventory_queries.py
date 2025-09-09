"""
Tests for inventory query functionality.
"""
import pytest
from unittest.mock import patch, MagicMock

from wholesale_agent.core.inventory_queries import InventoryQueryHandler


@pytest.mark.integration
class TestInventoryQueryHandler:
    """Test InventoryQueryHandler functionality."""
    
    @pytest.fixture
    def handler(self):
        """Create inventory query handler instance."""
        return InventoryQueryHandler()
    
    def test_get_product_stock_found(self, handler, sample_data):
        """Test getting stock for existing product."""
        # Mock the database session
        with patch('wholesale_agent.core.inventory_queries.db_manager.get_session') as mock_session:
            mock_session.return_value.__enter__.return_value = MagicMock()
            session = mock_session.return_value.__enter__.return_value
            
            # Mock product query result
            mock_product = MagicMock()
            mock_product.id = 1
            mock_product.sku = "ELE-1234-001"
            mock_product.name = "Wireless Bluetooth Headphones"
            mock_product.current_stock = 100
            mock_product.minimum_stock = 20
            mock_product.maximum_stock = 500
            mock_product.stock_status = "IN_STOCK"
            mock_product.is_low_stock = False
            mock_product.category.name = "Electronics"
            mock_product.supplier.name = "TechCorp"
            mock_product.cost_price = 45.0
            mock_product.wholesale_price = 65.0
            mock_product.retail_price = 99.99
            
            session.query.return_value.filter.return_value.first.return_value = mock_product
            session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
            
            result = handler.get_product_stock("wireless headphones")
            
            assert result['found'] is True
            assert result['product']['sku'] == "ELE-1234-001"
            assert result['product']['current_stock'] == 100
            assert result['product']['stock_status'] == "IN_STOCK"
    
    def test_get_product_stock_not_found(self, handler):
        """Test getting stock for non-existing product."""
        with patch('wholesale_agent.core.inventory_queries.db_manager.get_session') as mock_session:
            mock_session.return_value.__enter__.return_value = MagicMock()
            session = mock_session.return_value.__enter__.return_value
            
            session.query.return_value.filter.return_value.first.return_value = None
            
            result = handler.get_product_stock("nonexistent product")
            
            assert result['found'] is False
            assert 'message' in result
    
    def test_get_low_stock_products(self, handler):
        """Test getting low stock products."""
        with patch('wholesale_agent.core.inventory_queries.db_manager.get_session') as mock_session:
            mock_session.return_value.__enter__.return_value = MagicMock()
            session = mock_session.return_value.__enter__.return_value
            
            # Mock low stock products
            mock_products = []
            for i in range(3):
                mock_product = MagicMock()
                mock_product.sku = f"LOW-{i+1:04d}-001"
                mock_product.name = f"Low Stock Product {i+1}"
                mock_product.current_stock = 5
                mock_product.minimum_stock = 20
                mock_product.category.name = "Electronics"
                mock_product.supplier.name = "TechCorp"
                mock_product.wholesale_price = 10.0
                mock_product.cost_price = 8.0
                mock_products.append(mock_product)
            
            session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_products
            
            result = handler.get_low_stock_products(limit=10)
            
            assert result['count'] == 3
            assert len(result['products']) == 3
            
            for i, product in enumerate(result['products']):
                assert product['sku'] == f"LOW-{i+1:04d}-001"
                assert product['current_stock'] == 5
                assert product['minimum_stock'] == 20
                assert product['stock_deficit'] == 15  # 20 - 5
    
    def test_get_out_of_stock_products(self, handler):
        """Test getting out of stock products."""
        with patch('wholesale_agent.core.inventory_queries.db_manager.get_session') as mock_session:
            mock_session.return_value.__enter__.return_value = MagicMock()
            session = mock_session.return_value.__enter__.return_value
            
            # Mock out of stock products
            mock_products = []
            for i in range(2):
                mock_product = MagicMock()
                mock_product.sku = f"OUT-{i+1:04d}-001"
                mock_product.name = f"Out of Stock Product {i+1}"
                mock_product.current_stock = 0
                mock_product.category.name = "Electronics"
                mock_product.supplier.name = "TechCorp"
                mock_product.minimum_stock = 10
                mock_product.wholesale_price = 15.0
                mock_product.cost_price = 12.0
                mock_products.append(mock_product)
            
            session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_products
            
            result = handler.get_out_of_stock_products()
            
            assert result['count'] == 2
            assert len(result['products']) == 2
            
            for product in result['products']:
                assert product['current_stock'] == 0  # Implicitly tested by being out of stock
                assert product['reorder_value'] == 120.0  # 10 * 12.0
    
    def test_get_inventory_value(self, handler):
        """Test calculating inventory value."""
        with patch('wholesale_agent.core.inventory_queries.db_manager.get_session') as mock_session:
            mock_session.return_value.__enter__.return_value = MagicMock()
            session = mock_session.return_value.__enter__.return_value
            
            # Mock aggregate query result
            mock_result = MagicMock()
            mock_result.total_products = 100
            mock_result.total_units = 5000
            mock_result.cost_value = 25000.0
            mock_result.wholesale_value = 35000.0
            mock_result.retail_value = 50000.0
            
            session.query.return_value.filter.return_value.first.return_value = mock_result
            
            # Mock category breakdown
            mock_category_data = []
            categories = ["Electronics", "Clothing", "Home & Garden"]
            for i, cat in enumerate(categories):
                mock_cat = MagicMock()
                mock_cat.name = cat
                mock_cat.product_count = 30 + i * 10
                mock_cat.total_units = 1000 + i * 500
                mock_cat.category_value = 8000.0 + i * 2000
                mock_category_data.append(mock_cat)
            
            session.query.return_value.join.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = mock_category_data
            
            result = handler.get_inventory_value()
            
            assert result['summary']['total_products'] == 100
            assert result['summary']['cost_value'] == 25000.0
            assert result['summary']['potential_markup'] == 25000.0  # 50000 - 25000
            
            assert len(result['by_category']) == 3
            assert result['by_category'][0]['category'] == "Electronics"
    
    def test_get_movement_history(self, handler):
        """Test getting inventory movement history."""
        with patch('wholesale_agent.core.inventory_queries.db_manager.get_session') as mock_session:
            mock_session.return_value.__enter__.return_value = MagicMock()
            session = mock_session.return_value.__enter__.return_value
            
            # Mock movement data
            mock_movements = []
            movement_types = ['INBOUND', 'OUTBOUND', 'ADJUSTMENT']
            quantities = [50, -20, 5]
            
            for i, (mov_type, qty) in enumerate(zip(movement_types, quantities)):
                mock_movement = MagicMock()
                mock_movement.id = i + 1
                mock_movement.created_at.strftime.return_value = f"2024-01-{i+1:02d} 10:00"
                mock_movement.product.name = f"Test Product {i+1}"
                mock_movement.product.sku = f"TST-{i+1:04d}-001"
                mock_movement.movement_type = mov_type
                mock_movement.quantity = qty
                mock_movement.unit_cost = 10.0 if mov_type == 'INBOUND' else None
                mock_movement.reference_number = f"REF-{i+1:03d}"
                mock_movement.notes = f"Test movement {i+1}"
                mock_movements.append(mock_movement)
            
            session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_movements
            
            result = handler.get_movement_history(days=30)
            
            assert result['period'] == "Last 30 days"
            assert result['statistics']['total_movements'] == 3
            assert result['statistics']['inbound_quantity'] == 55  # 50 + 5
            assert result['statistics']['outbound_quantity'] == 20  # abs(-20)
            assert result['statistics']['net_change'] == 35  # 55 - 20
            
            assert len(result['movements']) == 3
            assert result['movements'][0]['movement_type'] == 'INBOUND'
    
    def test_get_inventory_summary(self, handler):
        """Test getting comprehensive inventory summary."""
        with patch('wholesale_agent.core.inventory_queries.db_manager.get_session') as mock_session:
            mock_session.return_value.__enter__.return_value = MagicMock()
            session = mock_session.return_value.__enter__.return_value
            
            # Mock various count queries
            session.query.return_value.filter.return_value.count.side_effect = [
                100,  # total_products
                10,   # total_categories  
                15,   # total_suppliers
                20,   # low_stock_count
                5,    # out_of_stock_count
                3,    # overstocked_count
                25,   # recent_movements
                2     # inactive_suppliers
            ]
            
            # Mock inventory value calculation
            with patch.object(handler, 'get_inventory_value') as mock_get_value:
                mock_get_value.return_value = {
                    'summary': {'cost_value': 75000.0}
                }
                
                result = handler.get_inventory_summary()
            
            assert result['overview']['total_products'] == 100
            assert result['overview']['inventory_value'] == 75000.0
            
            assert result['stock_status']['in_stock'] == 75  # 100 - 20 - 5
            assert result['stock_status']['low_stock'] == 20
            assert result['stock_status']['out_of_stock'] == 5
            assert result['stock_status']['overstocked'] == 3
            
            assert result['alerts']['needs_reorder'] == 25  # 20 + 5
            assert result['alerts']['excess_inventory'] == 3
            assert result['alerts']['inactive_suppliers'] == 2
    
    def test_execute_query_valid_type(self, handler):
        """Test executing a valid query type."""
        with patch.object(handler, 'get_inventory_summary') as mock_method:
            mock_method.return_value = {'test': 'data'}
            
            result = handler.execute_query('inventory_summary')
            
            assert result == {'test': 'data'}
            mock_method.assert_called_once()
    
    def test_execute_query_invalid_type(self, handler):
        """Test executing an invalid query type."""
        with pytest.raises(ValueError) as exc_info:
            handler.execute_query('invalid_query_type')
        
        assert "Unknown query type" in str(exc_info.value)


@pytest.mark.unit
class TestInventoryQueryMethods:
    """Test individual query methods with mocked data."""
    
    @pytest.fixture
    def handler(self):
        """Create handler instance."""
        return InventoryQueryHandler()
    
    def test_stock_forecast_with_data(self, handler):
        """Test stock forecast calculation with movement data."""
        with patch('wholesale_agent.core.inventory_queries.db_manager.get_session') as mock_session:
            mock_session.return_value.__enter__.return_value = MagicMock()
            session = mock_session.return_value.__enter__.return_value
            
            # Mock product
            mock_product = MagicMock()
            mock_product.name = "Test Product"
            mock_product.current_stock = 100
            mock_product.minimum_stock = 20
            
            session.query.return_value.filter.return_value.first.return_value = mock_product
            
            # Mock outbound movements (simulating sales)
            mock_movements = []
            for i in range(10):  # 10 sales movements
                mock_movement = MagicMock()
                mock_movement.quantity = -5  # 5 units sold each time
                mock_movements.append(mock_movement)
            
            session.query.return_value.filter.return_value.all.return_value = mock_movements
            
            result = handler.get_stock_forecast("test product", days=30)
            
            assert result['found'] is True
            assert result['avg_daily_consumption'] > 0
            assert 'projected_stock_in_30_days' in result
            assert 'recommendation' in result
            assert 'forecast_confidence' in result
    
    def test_stock_forecast_no_data(self, handler):
        """Test stock forecast with no movement data."""
        with patch('wholesale_agent.core.inventory_queries.db_manager.get_session') as mock_session:
            mock_session.return_value.__enter__.return_value = MagicMock()
            session = mock_session.return_value.__enter__.return_value
            
            # Mock product
            mock_product = MagicMock()
            mock_product.name = "Test Product"
            mock_product.current_stock = 100
            
            session.query.return_value.filter.return_value.first.return_value = mock_product
            session.query.return_value.filter.return_value.all.return_value = []  # No movements
            
            result = handler.get_stock_forecast("test product")
            
            assert result['found'] is True
            assert result['forecast'] == 'Insufficient data for forecast'
            assert 'No recent sales data' in result['recommendation']