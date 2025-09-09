"""
Test configuration and fixtures for wholesale agent tests.
"""
import pytest
import os
import tempfile
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from wholesale_agent.models import Base, db_manager
from wholesale_agent.models import Category, Supplier, Product, InventoryMovement
from wholesale_agent.utils.config import Config


@pytest.fixture(scope="session")
def test_config():
    """Create test configuration."""
    return Config(debug=True)


@pytest.fixture(scope="function")
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        test_db_path = f.name
    
    test_db_url = f"sqlite:///{test_db_path}"
    
    # Create test engine and session
    engine = create_engine(test_db_url, echo=False)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield SessionLocal
    
    # Cleanup
    engine.dispose()
    if os.path.exists(test_db_path):
        os.unlink(test_db_path)


@pytest.fixture
def test_session(temp_db):
    """Create test database session."""
    session = temp_db()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_category(test_session):
    """Create sample category for testing."""
    category = Category(
        name="Electronics",
        description="Electronic devices and accessories"
    )
    test_session.add(category)
    test_session.commit()
    test_session.refresh(category)
    return category


@pytest.fixture
def sample_supplier(test_session):
    """Create sample supplier for testing."""
    supplier = Supplier(
        name="TechCorp Wholesale",
        contact_email="orders@techcorp.com",
        contact_phone="1-800-123-4567",
        address="123 Tech Street, Silicon Valley, CA",
        tax_id="TAX-123456789",
        payment_terms="Net 30",
        is_active=True
    )
    test_session.add(supplier)
    test_session.commit()
    test_session.refresh(supplier)
    return supplier


@pytest.fixture
def sample_product(test_session, sample_category, sample_supplier):
    """Create sample product for testing."""
    product = Product(
        sku="ELE-1234-001",
        name="Wireless Bluetooth Headphones",
        description="High-quality wireless headphones with noise cancellation",
        category_id=sample_category.id,
        supplier_id=sample_supplier.id,
        cost_price=45.00,
        wholesale_price=65.00,
        retail_price=99.99,
        current_stock=100,
        minimum_stock=20,
        maximum_stock=500,
        weight=0.5,
        dimensions="20x15x8",
        barcode="1234567890123",
        is_active=True,
        is_discontinued=False
    )
    test_session.add(product)
    test_session.commit()
    test_session.refresh(product)
    return product


@pytest.fixture
def sample_inventory_movement(test_session, sample_product):
    """Create sample inventory movement for testing."""
    movement = InventoryMovement(
        product_id=sample_product.id,
        movement_type="INBOUND",
        quantity=50,
        unit_cost=45.00,
        reference_number="PO-123456",
        notes="Initial stock",
        from_location=None,
        to_location="Warehouse A"
    )
    test_session.add(movement)
    test_session.commit()
    test_session.refresh(movement)
    return movement


@pytest.fixture
def sample_data(test_session, sample_category, sample_supplier):
    """Create comprehensive sample data for testing."""
    # Create additional categories
    categories = [
        Category(name="Clothing", description="Apparel and accessories"),
        Category(name="Home & Garden", description="Home improvement items"),
    ]
    for cat in categories:
        test_session.add(cat)
    
    # Create additional suppliers
    suppliers = [
        Supplier(
            name="Fashion Plus",
            contact_email="orders@fashionplus.com",
            payment_terms="Net 15",
            is_active=True
        ),
        Supplier(
            name="Garden Supply Co",
            contact_email="sales@gardensupply.com",
            payment_terms="Net 45",
            is_active=False
        ),
    ]
    for sup in suppliers:
        test_session.add(sup)
    
    test_session.commit()
    
    # Create products
    products = [
        Product(
            sku="ELE-1235-001",
            name="USB-C Cable",
            category_id=sample_category.id,
            supplier_id=sample_supplier.id,
            cost_price=5.00,
            wholesale_price=8.50,
            retail_price=14.99,
            current_stock=5,  # Low stock
            minimum_stock=20,
            maximum_stock=200,
            is_active=True
        ),
        Product(
            sku="CLO-2001-001", 
            name="Cotton T-Shirt",
            category_id=categories[0].id,
            supplier_id=suppliers[0].id,
            cost_price=8.00,
            wholesale_price=14.00,
            retail_price=24.99,
            current_stock=0,  # Out of stock
            minimum_stock=10,
            maximum_stock=100,
            is_active=True
        ),
        Product(
            sku="HOM-3001-001",
            name="Garden Hose",
            category_id=categories[1].id,
            supplier_id=suppliers[1].id,
            cost_price=15.00,
            wholesale_price=25.00,
            retail_price=39.99,
            current_stock=200,  # Overstocked
            minimum_stock=10,
            maximum_stock=50,
            is_active=True
        ),
    ]
    
    for prod in products:
        test_session.add(prod)
    
    test_session.commit()
    
    # Create inventory movements
    movements = [
        InventoryMovement(
            product_id=products[0].id,
            movement_type="OUTBOUND",
            quantity=-15,
            reference_number="SO-001"
        ),
        InventoryMovement(
            product_id=products[1].id,
            movement_type="OUTBOUND", 
            quantity=-10,
            reference_number="SO-002"
        ),
        InventoryMovement(
            product_id=products[2].id,
            movement_type="INBOUND",
            quantity=150,
            reference_number="PO-789"
        ),
    ]
    
    for mov in movements:
        test_session.add(mov)
    
    test_session.commit()
    
    return {
        'categories': [sample_category] + categories,
        'suppliers': [sample_supplier] + suppliers,
        'products': products,
        'movements': movements
    }


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return "This is a mock response from the AI agent."


@pytest.fixture
def mock_llm_client(monkeypatch):
    """Mock LLM client for testing."""
    class MockLLMClient:
        def __init__(self, *args, **kwargs):
            pass
        
        def generate_response(self, prompt, system_prompt=None):
            return "Mock AI response based on the provided data."
        
        def is_available(self):
            return True
        
        def get_model_info(self):
            return {
                'provider': 'mock',
                'model': 'mock-model',
                'available': True
            }
    
    monkeypatch.setattr('wholesale_agent.core.llm_client.LLMClient', MockLLMClient)
    return MockLLMClient


# Pytest markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (slower, uses database)"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (may take several seconds)"
    )