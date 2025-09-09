"""
Inventory and product models for wholesale business.
"""
from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from .base import BaseModel


class Category(BaseModel):
    """Product category model."""
    __tablename__ = "categories"
    
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    # Self-referential relationship for category hierarchy
    parent = relationship("Category", remote_side="Category.id", backref="subcategories")
    products = relationship("Product", back_populates="category")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"


class Supplier(BaseModel):
    """Supplier model."""
    __tablename__ = "suppliers"
    
    name = Column(String(200), nullable=False)
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    address = Column(Text)
    tax_id = Column(String(50))
    payment_terms = Column(String(100))
    is_active = Column(Boolean, default=True)
    
    products = relationship("Product", back_populates="supplier")
    
    def __repr__(self):
        return f"<Supplier(id={self.id}, name='{self.name}')>"


class Product(BaseModel):
    """Product model."""
    __tablename__ = "products"
    
    sku = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    
    # Pricing
    cost_price = Column(Float, nullable=False)
    wholesale_price = Column(Float, nullable=False)
    retail_price = Column(Float, nullable=False)
    
    # Inventory tracking
    current_stock = Column(Integer, default=0, nullable=False)
    minimum_stock = Column(Integer, default=0, nullable=False)
    maximum_stock = Column(Integer, default=1000, nullable=False)
    
    # Product specifications
    weight = Column(Float)  # in kg
    dimensions = Column(String(100))  # LxWxH format
    barcode = Column(String(50), unique=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_discontinued = Column(Boolean, default=False)
    
    # Relationships
    category = relationship("Category", back_populates="products")
    supplier = relationship("Supplier", back_populates="products")
    inventory_movements = relationship("InventoryMovement", back_populates="product")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_product_sku_active', 'sku', 'is_active'),
        Index('idx_product_category_active', 'category_id', 'is_active'),
        Index('idx_product_supplier_active', 'supplier_id', 'is_active'),
    )
    
    @property
    def is_low_stock(self):
        """Check if product is below minimum stock level."""
        return self.current_stock <= self.minimum_stock
    
    @property
    def stock_status(self):
        """Get stock status as string."""
        if self.current_stock <= 0:
            return "OUT_OF_STOCK"
        elif self.is_low_stock:
            return "LOW_STOCK"
        elif self.current_stock >= self.maximum_stock:
            return "OVERSTOCKED"
        else:
            return "IN_STOCK"
    
    def __repr__(self):
        return f"<Product(id={self.id}, sku='{self.sku}', name='{self.name}', stock={self.current_stock})>"


class InventoryMovement(BaseModel):
    """Inventory movement tracking."""
    __tablename__ = "inventory_movements"
    
    MOVEMENT_TYPES = [
        'INBOUND',      # Stock received
        'OUTBOUND',     # Stock sold/shipped
        'ADJUSTMENT',   # Manual adjustment
        'RETURN',       # Customer return
        'DAMAGED',      # Damaged goods
        'TRANSFER'      # Transfer between locations
    ]
    
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    movement_type = Column(String(20), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Float)
    reference_number = Column(String(100))  # PO number, invoice number, etc.
    notes = Column(Text)
    
    # Location tracking (for future multi-warehouse support)
    from_location = Column(String(100))
    to_location = Column(String(100))
    
    product = relationship("Product", back_populates="inventory_movements")
    
    __table_args__ = (
        Index('idx_inventory_product_date', 'product_id', 'created_at'),
        Index('idx_inventory_type_date', 'movement_type', 'created_at'),
    )
    
    def __repr__(self):
        return f"<InventoryMovement(id={self.id}, product_id={self.product_id}, type='{self.movement_type}', qty={self.quantity})>"