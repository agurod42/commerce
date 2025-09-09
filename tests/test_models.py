"""
Tests for database models.
"""
import pytest
from datetime import datetime

from wholesale_agent.models import Category, Supplier, Product, InventoryMovement


@pytest.mark.unit
class TestCategory:
    """Test Category model."""
    
    def test_category_creation(self, test_session):
        """Test creating a category."""
        category = Category(
            name="Test Category",
            description="Test description"
        )
        test_session.add(category)
        test_session.commit()
        
        assert category.id is not None
        assert category.name == "Test Category"
        assert category.description == "Test description"
        assert category.created_at is not None
        assert category.updated_at is not None
    
    def test_category_repr(self, sample_category):
        """Test category string representation."""
        repr_str = repr(sample_category)
        assert "Category" in repr_str
        assert str(sample_category.id) in repr_str
        assert sample_category.name in repr_str
    
    def test_category_hierarchy(self, test_session):
        """Test category parent-child relationship."""
        parent = Category(name="Electronics")
        test_session.add(parent)
        test_session.commit()
        
        child = Category(name="Headphones", parent_id=parent.id)
        test_session.add(child)
        test_session.commit()
        
        test_session.refresh(parent)
        assert len(parent.subcategories) == 1
        assert parent.subcategories[0].name == "Headphones"
        assert child.parent.name == "Electronics"


@pytest.mark.unit
class TestSupplier:
    """Test Supplier model."""
    
    def test_supplier_creation(self, test_session):
        """Test creating a supplier."""
        supplier = Supplier(
            name="Test Supplier",
            contact_email="test@supplier.com",
            contact_phone="123-456-7890",
            payment_terms="Net 30",
            is_active=True
        )
        test_session.add(supplier)
        test_session.commit()
        
        assert supplier.id is not None
        assert supplier.name == "Test Supplier"
        assert supplier.is_active is True
    
    def test_supplier_repr(self, sample_supplier):
        """Test supplier string representation."""
        repr_str = repr(sample_supplier)
        assert "Supplier" in repr_str
        assert str(sample_supplier.id) in repr_str
        assert sample_supplier.name in repr_str


@pytest.mark.unit
class TestProduct:
    """Test Product model."""
    
    def test_product_creation(self, sample_product):
        """Test creating a product."""
        assert sample_product.id is not None
        assert sample_product.sku == "ELE-1234-001"
        assert sample_product.name == "Wireless Bluetooth Headphones"
        assert sample_product.current_stock == 100
    
    def test_product_repr(self, sample_product):
        """Test product string representation."""
        repr_str = repr(sample_product)
        assert "Product" in repr_str
        assert sample_product.sku in repr_str
        assert str(sample_product.current_stock) in repr_str
    
    def test_product_stock_properties(self, test_session, sample_category, sample_supplier):
        """Test product stock-related properties."""
        # Test low stock
        low_stock_product = Product(
            sku="TEST-LOW-001",
            name="Low Stock Product",
            category_id=sample_category.id,
            supplier_id=sample_supplier.id,
            cost_price=10.0,
            wholesale_price=15.0,
            retail_price=25.0,
            current_stock=5,
            minimum_stock=10,
            maximum_stock=100
        )
        
        assert low_stock_product.is_low_stock is True
        assert low_stock_product.stock_status == "LOW_STOCK"
        
        # Test out of stock
        out_of_stock_product = Product(
            sku="TEST-OUT-001",
            name="Out of Stock Product",
            category_id=sample_category.id,
            supplier_id=sample_supplier.id,
            cost_price=10.0,
            wholesale_price=15.0,
            retail_price=25.0,
            current_stock=0,
            minimum_stock=10,
            maximum_stock=100
        )
        
        assert out_of_stock_product.stock_status == "OUT_OF_STOCK"
        
        # Test overstocked
        overstocked_product = Product(
            sku="TEST-OVER-001",
            name="Overstocked Product",
            category_id=sample_category.id,
            supplier_id=sample_supplier.id,
            cost_price=10.0,
            wholesale_price=15.0,
            retail_price=25.0,
            current_stock=150,
            minimum_stock=10,
            maximum_stock=100
        )
        
        assert overstocked_product.stock_status == "OVERSTOCKED"
        
        # Test normal stock
        normal_product = Product(
            sku="TEST-NORM-001",
            name="Normal Product",
            category_id=sample_category.id,
            supplier_id=sample_supplier.id,
            cost_price=10.0,
            wholesale_price=15.0,
            retail_price=25.0,
            current_stock=50,
            minimum_stock=10,
            maximum_stock=100
        )
        
        assert normal_product.stock_status == "IN_STOCK"
        assert normal_product.is_low_stock is False
    
    def test_product_relationships(self, sample_product):
        """Test product relationships."""
        assert sample_product.category is not None
        assert sample_product.supplier is not None
        assert sample_product.category.name == "Electronics"
        assert sample_product.supplier.name == "TechCorp Wholesale"


@pytest.mark.unit
class TestInventoryMovement:
    """Test InventoryMovement model."""
    
    def test_movement_creation(self, sample_inventory_movement):
        """Test creating an inventory movement."""
        assert sample_inventory_movement.id is not None
        assert sample_inventory_movement.movement_type == "INBOUND"
        assert sample_inventory_movement.quantity == 50
        assert sample_inventory_movement.unit_cost == 45.00
    
    def test_movement_repr(self, sample_inventory_movement):
        """Test movement string representation."""
        repr_str = repr(sample_inventory_movement)
        assert "InventoryMovement" in repr_str
        assert str(sample_inventory_movement.product_id) in repr_str
        assert sample_inventory_movement.movement_type in repr_str
    
    def test_movement_types(self, test_session, sample_product):
        """Test different movement types."""
        movement_types = ['INBOUND', 'OUTBOUND', 'ADJUSTMENT', 'RETURN', 'DAMAGED']
        
        for movement_type in movement_types:
            movement = InventoryMovement(
                product_id=sample_product.id,
                movement_type=movement_type,
                quantity=10 if movement_type in ['INBOUND', 'RETURN'] else -10,
                reference_number=f"REF-{movement_type}"
            )
            test_session.add(movement)
        
        test_session.commit()
        
        # Verify all movements were created
        movements = test_session.query(InventoryMovement).filter(
            InventoryMovement.product_id == sample_product.id
        ).all()
        
        # +1 for the movement created by sample_inventory_movement fixture
        assert len(movements) == len(movement_types) + 1
    
    def test_movement_relationship(self, sample_inventory_movement, sample_product):
        """Test movement-product relationship."""
        assert sample_inventory_movement.product is not None
        assert sample_inventory_movement.product.id == sample_product.id
        assert sample_inventory_movement.product.name == sample_product.name


@pytest.mark.integration
class TestModelIntegration:
    """Integration tests for models working together."""
    
    def test_full_product_lifecycle(self, test_session, sample_category, sample_supplier):
        """Test complete product lifecycle with movements."""
        # Create product
        product = Product(
            sku="TEST-LIFECYCLE-001",
            name="Lifecycle Test Product",
            category_id=sample_category.id,
            supplier_id=sample_supplier.id,
            cost_price=20.0,
            wholesale_price=30.0,
            retail_price=45.0,
            current_stock=0,
            minimum_stock=5,
            maximum_stock=50
        )
        test_session.add(product)
        test_session.commit()
        
        # Initial stock receipt
        inbound = InventoryMovement(
            product_id=product.id,
            movement_type="INBOUND",
            quantity=30,
            unit_cost=20.0,
            reference_number="PO-001"
        )
        test_session.add(inbound)
        test_session.commit()
        
        # Update product stock
        product.current_stock += inbound.quantity
        test_session.commit()
        
        # Sales
        sales = [
            InventoryMovement(
                product_id=product.id,
                movement_type="OUTBOUND",
                quantity=-5,
                reference_number="SO-001"
            ),
            InventoryMovement(
                product_id=product.id,
                movement_type="OUTBOUND", 
                quantity=-10,
                reference_number="SO-002"
            )
        ]
        
        for sale in sales:
            test_session.add(sale)
            product.current_stock += sale.quantity  # Negative quantity
        
        test_session.commit()
        
        # Verify final state
        test_session.refresh(product)
        assert product.current_stock == 15  # 30 - 5 - 10
        assert product.stock_status == "IN_STOCK"
        
        # Check movement history
        movements = test_session.query(InventoryMovement).filter(
            InventoryMovement.product_id == product.id
        ).order_by(InventoryMovement.created_at).all()
        
        assert len(movements) == 3
        assert movements[0].movement_type == "INBOUND"
        assert movements[1].movement_type == "OUTBOUND"
        assert movements[2].movement_type == "OUTBOUND"
    
    def test_category_product_aggregation(self, sample_data):
        """Test aggregating products by category."""
        # This would typically be done with a query in the service layer
        # Here we're just testing that the relationships work
        electronics_category = sample_data['categories'][0]  # Electronics
        
        electronics_products = [p for p in electronics_category.products if p.is_active]
        assert len(electronics_products) >= 1
        
        total_value = sum(p.current_stock * p.cost_price for p in electronics_products)
        assert total_value > 0