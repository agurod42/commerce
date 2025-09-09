"""
Inventory management operations for adding, updating, and managing stock.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..models import db_manager, Product, Category, Supplier, InventoryMovement
from ..utils.logger import get_logger


class InventoryManager:
    """Handles inventory write operations and stock management."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def add_stock(self, product_identifier: str, quantity: int, 
                  cost_price: Optional[float] = None, reference: Optional[str] = None,
                  notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Add stock to a product.
        
        Args:
            product_identifier: SKU or product name
            quantity: Quantity to add (positive number)
            cost_price: Cost per unit (optional)
            reference: Reference number (PO, receipt, etc.)
            notes: Additional notes
            
        Returns:
            Dict with operation result
        """
        if quantity <= 0:
            return {
                'success': False,
                'error': 'Quantity must be positive'
            }
        
        try:
            with db_manager.get_session() as session:
                # Find product
                product = self._find_product(session, product_identifier)
                if not product:
                    return {
                        'success': False,
                        'error': f'Product "{product_identifier}" not found'
                    }
                
                # Record inventory movement
                movement = InventoryMovement(
                    product_id=product.id,
                    movement_type='INBOUND',
                    quantity=quantity,
                    unit_cost=cost_price,
                    reference_number=reference or f'STOCK_ADD_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                    notes=notes,
                    to_location='Warehouse A'
                )
                session.add(movement)
                
                # Update product stock
                old_stock = product.current_stock
                product.current_stock += quantity
                
                session.commit()
                
                self.logger.info(f"Added {quantity} units to {product.sku}")
                
                return {
                    'success': True,
                    'product': {
                        'sku': product.sku,
                        'name': product.name,
                        'old_stock': old_stock,
                        'new_stock': product.current_stock,
                        'added_quantity': quantity
                    },
                    'movement_id': movement.id,
                    'message': f'Successfully added {quantity} units to {product.name}'
                }
                
        except Exception as e:
            self.logger.error(f"Error adding stock: {e}")
            return {
                'success': False,
                'error': f'Failed to add stock: {str(e)}'
            }
    
    def remove_stock(self, product_identifier: str, quantity: int,
                     reason: str = 'OUTBOUND', reference: Optional[str] = None,
                     notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Remove stock from a product.
        
        Args:
            product_identifier: SKU or product name
            quantity: Quantity to remove (positive number)
            reason: Reason for removal (OUTBOUND, DAMAGED, ADJUSTMENT)
            reference: Reference number
            notes: Additional notes
            
        Returns:
            Dict with operation result
        """
        if quantity <= 0:
            return {
                'success': False,
                'error': 'Quantity must be positive'
            }
        
        valid_reasons = ['OUTBOUND', 'DAMAGED', 'ADJUSTMENT', 'RETURN', 'TRANSFER']
        if reason not in valid_reasons:
            return {
                'success': False,
                'error': f'Invalid reason. Must be one of: {", ".join(valid_reasons)}'
            }
        
        try:
            with db_manager.get_session() as session:
                # Find product
                product = self._find_product(session, product_identifier)
                if not product:
                    return {
                        'success': False,
                        'error': f'Product "{product_identifier}" not found'
                    }
                
                # Check if enough stock available
                if product.current_stock < quantity:
                    return {
                        'success': False,
                        'error': f'Insufficient stock. Available: {product.current_stock}, Requested: {quantity}'
                    }
                
                # Record inventory movement
                movement = InventoryMovement(
                    product_id=product.id,
                    movement_type=reason,
                    quantity=-quantity,  # Negative for stock reduction
                    reference_number=reference or f'STOCK_REMOVE_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                    notes=notes,
                    from_location='Warehouse A'
                )
                session.add(movement)
                
                # Update product stock
                old_stock = product.current_stock
                product.current_stock -= quantity
                
                session.commit()
                
                self.logger.info(f"Removed {quantity} units from {product.sku}")
                
                return {
                    'success': True,
                    'product': {
                        'sku': product.sku,
                        'name': product.name,
                        'old_stock': old_stock,
                        'new_stock': product.current_stock,
                        'removed_quantity': quantity
                    },
                    'movement_id': movement.id,
                    'message': f'Successfully removed {quantity} units from {product.name}',
                    'warning': 'Low stock warning!' if product.current_stock <= product.minimum_stock else None
                }
                
        except Exception as e:
            self.logger.error(f"Error removing stock: {e}")
            return {
                'success': False,
                'error': f'Failed to remove stock: {str(e)}'
            }
    
    def adjust_stock(self, product_identifier: str, new_quantity: int,
                     reason: Optional[str] = None, reference: Optional[str] = None) -> Dict[str, Any]:
        """
        Set stock to a specific quantity (absolute adjustment).
        
        Args:
            product_identifier: SKU or product name
            new_quantity: New stock quantity
            reason: Reason for adjustment
            reference: Reference number
            
        Returns:
            Dict with operation result
        """
        if new_quantity < 0:
            return {
                'success': False,
                'error': 'Stock quantity cannot be negative'
            }
        
        try:
            with db_manager.get_session() as session:
                # Find product
                product = self._find_product(session, product_identifier)
                if not product:
                    return {
                        'success': False,
                        'error': f'Product "{product_identifier}" not found'
                    }
                
                old_stock = product.current_stock
                adjustment = new_quantity - old_stock
                
                if adjustment == 0:
                    return {
                        'success': True,
                        'message': f'Stock already at {new_quantity} units - no adjustment needed'
                    }
                
                # Record inventory movement
                movement = InventoryMovement(
                    product_id=product.id,
                    movement_type='ADJUSTMENT',
                    quantity=adjustment,
                    reference_number=reference or f'STOCK_ADJ_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                    notes=reason or f'Stock adjusted from {old_stock} to {new_quantity}'
                )
                session.add(movement)
                
                # Update product stock
                product.current_stock = new_quantity
                
                session.commit()
                
                self.logger.info(f"Adjusted {product.sku} stock from {old_stock} to {new_quantity}")
                
                return {
                    'success': True,
                    'product': {
                        'sku': product.sku,
                        'name': product.name,
                        'old_stock': old_stock,
                        'new_stock': new_quantity,
                        'adjustment': adjustment
                    },
                    'movement_id': movement.id,
                    'message': f'Successfully adjusted {product.name} stock to {new_quantity} units'
                }
                
        except Exception as e:
            self.logger.error(f"Error adjusting stock: {e}")
            return {
                'success': False,
                'error': f'Failed to adjust stock: {str(e)}'
            }
    
    def create_product(self, sku: str, name: str, category_name: str, supplier_name: str,
                      cost_price: float, wholesale_price: float, retail_price: float,
                      initial_stock: int = 0, minimum_stock: int = 10, maximum_stock: int = 1000,
                      description: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Create a new product.
        
        Args:
            sku: Product SKU (must be unique)
            name: Product name
            category_name: Category name
            supplier_name: Supplier name
            cost_price: Cost price per unit
            wholesale_price: Wholesale price per unit
            retail_price: Retail price per unit
            initial_stock: Initial stock quantity
            minimum_stock: Minimum stock level
            maximum_stock: Maximum stock level
            description: Product description
            **kwargs: Additional product fields
            
        Returns:
            Dict with operation result
        """
        try:
            with db_manager.get_session() as session:
                # Check if SKU already exists
                existing = session.query(Product).filter(Product.sku == sku).first()
                if existing:
                    return {
                        'success': False,
                        'error': f'Product with SKU "{sku}" already exists'
                    }
                
                # Find or create category
                category = session.query(Category).filter(Category.name == category_name).first()
                if not category:
                    category = Category(name=category_name, description=f'Auto-created for {name}')
                    session.add(category)
                    session.flush()  # Get ID
                
                # Find or create supplier
                supplier = session.query(Supplier).filter(Supplier.name == supplier_name).first()
                if not supplier:
                    supplier = Supplier(name=supplier_name, is_active=True)
                    session.add(supplier)
                    session.flush()  # Get ID
                
                # Create product
                product = Product(
                    sku=sku,
                    name=name,
                    description=description,
                    category_id=category.id,
                    supplier_id=supplier.id,
                    cost_price=cost_price,
                    wholesale_price=wholesale_price,
                    retail_price=retail_price,
                    current_stock=initial_stock,
                    minimum_stock=minimum_stock,
                    maximum_stock=maximum_stock,
                    is_active=True,
                    **{k: v for k, v in kwargs.items() if hasattr(Product, k)}
                )
                session.add(product)
                
                # Record initial stock if any
                if initial_stock > 0:
                    movement = InventoryMovement(
                        product_id=product.id,
                        movement_type='INBOUND',
                        quantity=initial_stock,
                        unit_cost=cost_price,
                        reference_number=f'INITIAL_STOCK_{sku}',
                        notes='Initial stock for new product'
                    )
                    session.add(movement)
                
                session.commit()
                
                self.logger.info(f"Created new product: {sku}")
                
                return {
                    'success': True,
                    'product': {
                        'id': product.id,
                        'sku': sku,
                        'name': name,
                        'category': category_name,
                        'supplier': supplier_name,
                        'initial_stock': initial_stock
                    },
                    'message': f'Successfully created product "{name}" with SKU {sku}'
                }
                
        except IntegrityError as e:
            return {
                'success': False,
                'error': f'Database constraint violation: {str(e)}'
            }
        except Exception as e:
            self.logger.error(f"Error creating product: {e}")
            return {
                'success': False,
                'error': f'Failed to create product: {str(e)}'
            }
    
    def update_product_prices(self, product_identifier: str, cost_price: Optional[float] = None,
                            wholesale_price: Optional[float] = None, retail_price: Optional[float] = None) -> Dict[str, Any]:
        """Update product prices."""
        try:
            with db_manager.get_session() as session:
                product = self._find_product(session, product_identifier)
                if not product:
                    return {
                        'success': False,
                        'error': f'Product "{product_identifier}" not found'
                    }
                
                old_prices = {
                    'cost_price': product.cost_price,
                    'wholesale_price': product.wholesale_price,
                    'retail_price': product.retail_price
                }
                
                # Update prices
                if cost_price is not None:
                    product.cost_price = cost_price
                if wholesale_price is not None:
                    product.wholesale_price = wholesale_price
                if retail_price is not None:
                    product.retail_price = retail_price
                
                session.commit()
                
                return {
                    'success': True,
                    'product': {
                        'sku': product.sku,
                        'name': product.name,
                        'old_prices': old_prices,
                        'new_prices': {
                            'cost_price': product.cost_price,
                            'wholesale_price': product.wholesale_price,
                            'retail_price': product.retail_price
                        }
                    },
                    'message': f'Successfully updated prices for {product.name}'
                }
                
        except Exception as e:
            self.logger.error(f"Error updating prices: {e}")
            return {
                'success': False,
                'error': f'Failed to update prices: {str(e)}'
            }
    
    def _find_product(self, session: Session, identifier: str) -> Optional[Product]:
        """Find product by SKU or name."""
        # Try exact SKU match first
        product = session.query(Product).filter(Product.sku == identifier).first()
        if product:
            return product
        
        # Try case-insensitive name match
        product = session.query(Product).filter(Product.name.ilike(identifier)).first()
        if product:
            return product
        
        # Try partial name match
        product = session.query(Product).filter(Product.name.ilike(f'%{identifier}%')).first()
        return product
    
    def get_stock_movements(self, product_identifier: str, limit: int = 10) -> Dict[str, Any]:
        """Get recent stock movements for a product."""
        try:
            with db_manager.get_session() as session:
                product = self._find_product(session, product_identifier)
                if not product:
                    return {
                        'success': False,
                        'error': f'Product "{product_identifier}" not found'
                    }
                
                movements = session.query(InventoryMovement).filter(
                    InventoryMovement.product_id == product.id
                ).order_by(InventoryMovement.created_at.desc()).limit(limit).all()
                
                return {
                    'success': True,
                    'product': {
                        'sku': product.sku,
                        'name': product.name,
                        'current_stock': product.current_stock
                    },
                    'movements': [
                        {
                            'id': m.id,
                            'date': m.created_at.strftime('%Y-%m-%d %H:%M'),
                            'type': m.movement_type,
                            'quantity': m.quantity,
                            'reference': m.reference_number,
                            'notes': m.notes
                        }
                        for m in movements
                    ]
                }
                
        except Exception as e:
            self.logger.error(f"Error getting movements: {e}")
            return {
                'success': False,
                'error': f'Failed to get movements: {str(e)}'
            }