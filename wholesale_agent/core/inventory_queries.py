"""
Specialized inventory query handlers for the wholesale agent.
"""
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import func, and_, or_, desc, asc
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..models import db_manager, Product, Category, Supplier, InventoryMovement


class InventoryQueryHandler:
    """Handles specialized inventory queries."""
    
    def __init__(self):
        self.query_handlers = {
            'stock_level': self.get_product_stock,
            'low_stock': self.get_low_stock_products,
            'out_of_stock': self.get_out_of_stock_products,
            'overstocked': self.get_overstocked_products,
            'inventory_value': self.get_inventory_value,
            'category_inventory': self.get_category_inventory,
            'supplier_inventory': self.get_supplier_inventory,
            'movement_history': self.get_movement_history,
            'stock_forecast': self.get_stock_forecast,
            'inventory_summary': self.get_inventory_summary
        }
    
    def execute_query(self, query_type: str, **kwargs) -> Dict[str, Any]:
        """Execute a specific inventory query."""
        if query_type in self.query_handlers:
            return self.query_handlers[query_type](**kwargs)
        else:
            raise ValueError(f"Unknown query type: {query_type}")
    
    def get_product_stock(self, product_identifier: str) -> Dict[str, Any]:
        """Get stock information for a specific product."""
        with db_manager.get_session() as session:
            # Try to find product by SKU first, then by name
            product = session.query(Product).filter(
                or_(
                    Product.sku.ilike(f'%{product_identifier}%'),
                    Product.name.ilike(f'%{product_identifier}%')
                )
            ).first()
            
            if not product:
                return {
                    'found': False,
                    'message': f"Product '{product_identifier}' not found"
                }
            
            # Get recent movements
            recent_movements = session.query(InventoryMovement).filter(
                InventoryMovement.product_id == product.id
            ).order_by(desc(InventoryMovement.created_at)).limit(5).all()
            
            return {
                'found': True,
                'product': {
                    'id': product.id,
                    'sku': product.sku,
                    'name': product.name,
                    'current_stock': product.current_stock,
                    'minimum_stock': product.minimum_stock,
                    'maximum_stock': product.maximum_stock,
                    'stock_status': product.stock_status,
                    'is_low_stock': product.is_low_stock,
                    'category': product.category.name,
                    'supplier': product.supplier.name,
                    'cost_price': product.cost_price,
                    'wholesale_price': product.wholesale_price,
                    'retail_price': product.retail_price,
                    'inventory_value': product.current_stock * product.cost_price
                },
                'recent_movements': [
                    {
                        'date': m.created_at.strftime('%Y-%m-%d %H:%M'),
                        'type': m.movement_type,
                        'quantity': m.quantity,
                        'reference': m.reference_number,
                        'notes': m.notes
                    }
                    for m in recent_movements
                ]
            }
    
    def get_low_stock_products(self, limit: int = 50) -> Dict[str, Any]:
        """Get products with low stock levels."""
        with db_manager.get_session() as session:
            products = session.query(Product).filter(
                and_(
                    Product.is_active == True,
                    Product.current_stock <= Product.minimum_stock
                )
            ).order_by(asc(Product.current_stock)).limit(limit).all()
            
            return {
                'count': len(products),
                'products': [
                    {
                        'sku': p.sku,
                        'name': p.name,
                        'current_stock': p.current_stock,
                        'minimum_stock': p.minimum_stock,
                        'stock_deficit': p.minimum_stock - p.current_stock,
                        'category': p.category.name,
                        'supplier': p.supplier.name,
                        'wholesale_price': p.wholesale_price,
                        'reorder_value': (p.minimum_stock - p.current_stock) * p.cost_price
                    }
                    for p in products
                ]
            }
    
    def get_out_of_stock_products(self, limit: int = 50) -> Dict[str, Any]:
        """Get products that are completely out of stock."""
        with db_manager.get_session() as session:
            products = session.query(Product).filter(
                and_(
                    Product.is_active == True,
                    Product.current_stock <= 0
                )
            ).order_by(Product.name).limit(limit).all()
            
            return {
                'count': len(products),
                'products': [
                    {
                        'sku': p.sku,
                        'name': p.name,
                        'category': p.category.name,
                        'supplier': p.supplier.name,
                        'minimum_stock': p.minimum_stock,
                        'wholesale_price': p.wholesale_price,
                        'reorder_value': p.minimum_stock * p.cost_price
                    }
                    for p in products
                ]
            }
    
    def get_overstocked_products(self, limit: int = 50) -> Dict[str, Any]:
        """Get products that are overstocked."""
        with db_manager.get_session() as session:
            products = session.query(Product).filter(
                and_(
                    Product.is_active == True,
                    Product.current_stock >= Product.maximum_stock
                )
            ).order_by(desc(Product.current_stock)).limit(limit).all()
            
            return {
                'count': len(products),
                'products': [
                    {
                        'sku': p.sku,
                        'name': p.name,
                        'current_stock': p.current_stock,
                        'maximum_stock': p.maximum_stock,
                        'excess_stock': p.current_stock - p.maximum_stock,
                        'category': p.category.name,
                        'supplier': p.supplier.name,
                        'tied_up_capital': (p.current_stock - p.maximum_stock) * p.cost_price
                    }
                    for p in products
                ]
            }
    
    def get_inventory_value(self, category_id: Optional[int] = None) -> Dict[str, Any]:
        """Calculate total inventory value, optionally filtered by category."""
        with db_manager.get_session() as session:
            query = session.query(
                func.count(Product.id).label('total_products'),
                func.sum(Product.current_stock).label('total_units'),
                func.sum(Product.current_stock * Product.cost_price).label('cost_value'),
                func.sum(Product.current_stock * Product.wholesale_price).label('wholesale_value'),
                func.sum(Product.current_stock * Product.retail_price).label('retail_value')
            ).filter(Product.is_active == True)
            
            if category_id:
                query = query.filter(Product.category_id == category_id)
            
            result = query.first()
            
            # Get value by category breakdown
            category_breakdown = session.query(
                Category.name,
                func.count(Product.id).label('product_count'),
                func.sum(Product.current_stock).label('total_units'),
                func.sum(Product.current_stock * Product.cost_price).label('category_value')
            ).join(Product).filter(Product.is_active == True).group_by(
                Category.name
            ).order_by(desc('category_value')).all()
            
            return {
                'summary': {
                    'total_products': result.total_products or 0,
                    'total_units': result.total_units or 0,
                    'cost_value': result.cost_value or 0,
                    'wholesale_value': result.wholesale_value or 0,
                    'retail_value': result.retail_value or 0,
                    'potential_markup': (result.retail_value or 0) - (result.cost_value or 0)
                },
                'by_category': [
                    {
                        'category': cb.name,
                        'product_count': cb.product_count,
                        'total_units': cb.total_units or 0,
                        'value': cb.category_value or 0
                    }
                    for cb in category_breakdown
                ]
            }
    
    def get_category_inventory(self, category_name: str) -> Dict[str, Any]:
        """Get inventory information for a specific category."""
        with db_manager.get_session() as session:
            category = session.query(Category).filter(
                Category.name.ilike(f'%{category_name}%')
            ).first()
            
            if not category:
                return {
                    'found': False,
                    'message': f"Category '{category_name}' not found"
                }
            
            products = session.query(Product).filter(
                and_(
                    Product.category_id == category.id,
                    Product.is_active == True
                )
            ).order_by(desc(Product.current_stock * Product.cost_price)).all()
            
            # Calculate category statistics
            total_products = len(products)
            total_units = sum(p.current_stock for p in products)
            total_value = sum(p.current_stock * p.cost_price for p in products)
            low_stock_count = sum(1 for p in products if p.is_low_stock)
            out_of_stock_count = sum(1 for p in products if p.current_stock <= 0)
            
            return {
                'found': True,
                'category': {
                    'name': category.name,
                    'description': category.description,
                    'total_products': total_products,
                    'total_units': total_units,
                    'total_value': total_value,
                    'low_stock_count': low_stock_count,
                    'out_of_stock_count': out_of_stock_count
                },
                'top_products': [
                    {
                        'sku': p.sku,
                        'name': p.name,
                        'current_stock': p.current_stock,
                        'stock_status': p.stock_status,
                        'value': p.current_stock * p.cost_price,
                        'supplier': p.supplier.name
                    }
                    for p in products[:10]
                ]
            }
    
    def get_supplier_inventory(self, supplier_name: str) -> Dict[str, Any]:
        """Get inventory information for products from a specific supplier."""
        with db_manager.get_session() as session:
            supplier = session.query(Supplier).filter(
                Supplier.name.ilike(f'%{supplier_name}%')
            ).first()
            
            if not supplier:
                return {
                    'found': False,
                    'message': f"Supplier '{supplier_name}' not found"
                }
            
            products = session.query(Product).filter(
                and_(
                    Product.supplier_id == supplier.id,
                    Product.is_active == True
                )
            ).order_by(desc(Product.current_stock * Product.cost_price)).all()
            
            # Calculate supplier statistics
            total_products = len(products)
            total_units = sum(p.current_stock for p in products)
            total_value = sum(p.current_stock * p.cost_price for p in products)
            low_stock_count = sum(1 for p in products if p.is_low_stock)
            
            return {
                'found': True,
                'supplier': {
                    'name': supplier.name,
                    'contact_email': supplier.contact_email,
                    'payment_terms': supplier.payment_terms,
                    'is_active': supplier.is_active,
                    'total_products': total_products,
                    'total_units': total_units,
                    'total_value': total_value,
                    'low_stock_count': low_stock_count
                },
                'products': [
                    {
                        'sku': p.sku,
                        'name': p.name,
                        'current_stock': p.current_stock,
                        'minimum_stock': p.minimum_stock,
                        'stock_status': p.stock_status,
                        'category': p.category.name,
                        'cost_price': p.cost_price,
                        'wholesale_price': p.wholesale_price
                    }
                    for p in products[:20]
                ]
            }
    
    def get_movement_history(self, days: int = 30, movement_type: Optional[str] = None, 
                           limit: int = 100) -> Dict[str, Any]:
        """Get inventory movement history."""
        with db_manager.get_session() as session:
            start_date = datetime.now() - timedelta(days=days)
            
            query = session.query(InventoryMovement).filter(
                InventoryMovement.created_at >= start_date
            )
            
            if movement_type:
                query = query.filter(InventoryMovement.movement_type == movement_type.upper())
            
            movements = query.order_by(
                desc(InventoryMovement.created_at)
            ).limit(limit).all()
            
            # Calculate statistics
            total_movements = len(movements)
            inbound_qty = sum(m.quantity for m in movements if m.quantity > 0)
            outbound_qty = abs(sum(m.quantity for m in movements if m.quantity < 0))
            
            return {
                'period': f"Last {days} days",
                'statistics': {
                    'total_movements': total_movements,
                    'inbound_quantity': inbound_qty,
                    'outbound_quantity': outbound_qty,
                    'net_change': inbound_qty - outbound_qty
                },
                'movements': [
                    {
                        'id': m.id,
                        'date': m.created_at.strftime('%Y-%m-%d %H:%M'),
                        'product_name': m.product.name,
                        'product_sku': m.product.sku,
                        'movement_type': m.movement_type,
                        'quantity': m.quantity,
                        'unit_cost': m.unit_cost,
                        'reference_number': m.reference_number,
                        'notes': m.notes
                    }
                    for m in movements
                ]
            }
    
    def get_inventory_summary(self) -> Dict[str, Any]:
        """Get comprehensive inventory summary."""
        with db_manager.get_session() as session:
            # Basic counts
            total_products = session.query(Product).filter(Product.is_active == True).count()
            total_categories = session.query(Category).count()
            total_suppliers = session.query(Supplier).filter(Supplier.is_active == True).count()
            
            # Stock status counts
            low_stock_count = session.query(Product).filter(
                and_(
                    Product.is_active == True,
                    Product.current_stock <= Product.minimum_stock
                )
            ).count()
            
            out_of_stock_count = session.query(Product).filter(
                and_(
                    Product.is_active == True,
                    Product.current_stock <= 0
                )
            ).count()
            
            overstocked_count = session.query(Product).filter(
                and_(
                    Product.is_active == True,
                    Product.current_stock >= Product.maximum_stock
                )
            ).count()
            
            # Value calculations
            inventory_value = self.get_inventory_value()
            
            # Recent activity
            recent_movements = session.query(InventoryMovement).filter(
                InventoryMovement.created_at >= datetime.now() - timedelta(days=7)
            ).count()
            
            return {
                'overview': {
                    'total_products': total_products,
                    'total_categories': total_categories,
                    'total_suppliers': total_suppliers,
                    'inventory_value': inventory_value['summary']['cost_value']
                },
                'stock_status': {
                    'in_stock': total_products - low_stock_count - out_of_stock_count,
                    'low_stock': low_stock_count,
                    'out_of_stock': out_of_stock_count,
                    'overstocked': overstocked_count
                },
                'recent_activity': {
                    'movements_last_7_days': recent_movements
                },
                'alerts': {
                    'needs_reorder': low_stock_count + out_of_stock_count,
                    'excess_inventory': overstocked_count,
                    'inactive_suppliers': session.query(Supplier).filter(
                        Supplier.is_active == False
                    ).count()
                }
            }
    
    def get_stock_forecast(self, product_identifier: str, days: int = 30) -> Dict[str, Any]:
        """Get stock forecast based on historical movement data."""
        with db_manager.get_session() as session:
            # Find product
            product = session.query(Product).filter(
                or_(
                    Product.sku.ilike(f'%{product_identifier}%'),
                    Product.name.ilike(f'%{product_identifier}%')
                )
            ).first()
            
            if not product:
                return {
                    'found': False,
                    'message': f"Product '{product_identifier}' not found"
                }
            
            # Get historical outbound movements (sales)
            start_date = datetime.now() - timedelta(days=90)  # Use 90 days of history
            outbound_movements = session.query(InventoryMovement).filter(
                and_(
                    InventoryMovement.product_id == product.id,
                    InventoryMovement.movement_type == 'OUTBOUND',
                    InventoryMovement.created_at >= start_date
                )
            ).all()
            
            if not outbound_movements:
                return {
                    'found': True,
                    'product_name': product.name,
                    'current_stock': product.current_stock,
                    'forecast': 'Insufficient data for forecast',
                    'recommendation': 'No recent sales data available'
                }
            
            # Calculate average daily consumption
            total_consumed = sum(abs(m.quantity) for m in outbound_movements)
            avg_daily_consumption = total_consumed / 90
            
            # Forecast
            days_until_stockout = product.current_stock / avg_daily_consumption if avg_daily_consumption > 0 else float('inf')
            projected_stock = max(0, product.current_stock - (avg_daily_consumption * days))
            
            # Recommendation
            if days_until_stockout <= product.minimum_stock:
                recommendation = "URGENT: Reorder immediately"
            elif days_until_stockout <= 14:
                recommendation = "Reorder recommended within next week"
            elif projected_stock <= product.minimum_stock:
                recommendation = f"Reorder recommended before {days} days"
            else:
                recommendation = "Stock levels adequate"
            
            return {
                'found': True,
                'product_name': product.name,
                'current_stock': product.current_stock,
                'minimum_stock': product.minimum_stock,
                'avg_daily_consumption': round(avg_daily_consumption, 2),
                'days_until_stockout': round(days_until_stockout, 1) if days_until_stockout != float('inf') else "Never (no consumption)",
                'projected_stock_in_30_days': round(projected_stock, 0),
                'recommendation': recommendation,
                'forecast_confidence': 'High' if len(outbound_movements) >= 10 else 'Low'
            }