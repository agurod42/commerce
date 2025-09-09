"""
Action executor for wholesale agent.
Executes business operations based on analyzed intent.
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from ..models import db_manager, Product, Category, Supplier, InventoryMovement
from .inventory_manager import InventoryManager
from .intent_analyzer import IntentResult


@dataclass
class ActionResult:
    """Result of executing an action."""
    success: bool
    data: Any = None
    message: str = ""
    error: Optional[str] = None
    action_type: str = ""


class ActionExecutor:
    """Executes business actions based on intent analysis."""
    
    def __init__(self):
        self.inventory_manager = InventoryManager()
        self.logger = logging.getLogger(__name__)
    
    def execute_action(self, intent_result: IntentResult) -> ActionResult:
        """Execute action based on analyzed intent."""
        try:
            if intent_result.needs_clarification:
                return ActionResult(
                    success=True,
                    action_type="clarification",
                    message=intent_result.clarification_question or "Could you please provide more details?"
                )
            
            intent_type = intent_result.intent_type
            entities = intent_result.entities
            
            # Route to appropriate action handler
            if intent_type == "inventory_query":
                return self._handle_inventory_query(entities)
            elif intent_type == "product_search":
                return self._handle_product_search(entities)
            elif intent_type == "inventory_management":
                return self._handle_inventory_management(entities)
            elif intent_type == "inventory_history":
                return self._handle_inventory_history(entities)
            elif intent_type == "analytics":
                return self._handle_analytics(entities)
            elif intent_type == "supplier_query":
                return self._handle_supplier_query(entities)
            elif intent_type == "price_query":
                return self._handle_price_query(entities)
            elif intent_type == "help_capabilities":
                return self._handle_help_capabilities(entities)
            elif intent_type == "low_stock_alert":
                return self._handle_low_stock_alert(entities)
            else:
                return ActionResult(
                    success=False,
                    action_type="unknown",
                    error=f"Unknown intent type: {intent_type}"
                )
                
        except Exception as e:
            self.logger.error(f"Action execution error: {str(e)}")
            return ActionResult(
                success=False,
                action_type="error",
                error=str(e)
            )
    
    def _handle_inventory_query(self, entities: Dict[str, Any]) -> ActionResult:
        """Handle inventory and stock queries."""
        with db_manager.get_session() as session:
            product_name = entities.get('product_name')
            category = entities.get('category')
            action = entities.get('action', '').lower()
            
            # Check if this is a "list all products" or general inventory query
            is_general_query = (
                (action == 'list' and (category and 'all' in category.lower())) or
                any(word in str(entities.values()).lower() for word in ['all products', 'every product', 'entire stock', 'total inventory']) or
                (not product_name and not category and not action)  # No specific entities = general query
            )
            
            if is_general_query:
                
                # Get all active products with stock information  
                all_products = session.query(Product).filter(
                    Product.is_active == True
                ).order_by(Product.name).limit(50).all()  # Limit to 50 for performance
                
                product_data = [
                    {
                        'id': p.id,
                        'sku': p.sku,
                        'name': p.name,
                        'current_stock': p.current_stock,
                        'minimum_stock': p.minimum_stock,
                        'stock_status': p.stock_status,
                        'category': p.category.name,
                        'supplier': p.supplier.name,
                        'wholesale_price': float(p.wholesale_price),
                        'retail_price': float(p.retail_price) if p.retail_price else None
                    }
                    for p in all_products
                ]
                
                return ActionResult(
                    success=True,
                    action_type="inventory_listing",
                    data=product_data,
                    message=f"Retrieved {len(all_products)} products with stock information"
                )
            
            # Specific product query
            if product_name:
                products = session.query(Product).filter(
                    and_(
                        Product.is_active == True,
                        Product.name.ilike(f'%{product_name}%')
                    )
                ).limit(10).all()
                
                if products:
                    product_data = [
                        {
                            'id': p.id,
                            'sku': p.sku,
                            'name': p.name,
                            'current_stock': p.current_stock,
                            'minimum_stock': p.minimum_stock,
                            'stock_status': p.stock_status,
                            'category': p.category.name,
                            'supplier': p.supplier.name,
                            'wholesale_price': float(p.wholesale_price),
                            'retail_price': float(p.retail_price) if p.retail_price else None
                        }
                        for p in products
                    ]
                    
                    return ActionResult(
                        success=True,
                        action_type="inventory_query",
                        data=product_data,
                        message=f"Found {len(products)} products matching '{product_name}'"
                    )
                else:
                    return ActionResult(
                        success=True,
                        action_type="inventory_query",
                        data=[],
                        message=f"No products found matching '{product_name}'"
                    )
            
            # Category-based query
            elif category:
                category_obj = session.query(Category).filter(
                    Category.name.ilike(f'%{category}%')
                ).first()
                
                if category_obj:
                    products = session.query(Product).filter(
                        and_(
                            Product.is_active == True,
                            Product.category_id == category_obj.id
                        )
                    ).limit(50).all()
                    
                    product_data = [
                        {
                            'sku': p.sku,
                            'name': p.name,
                            'current_stock': p.current_stock,
                            'stock_status': p.stock_status
                        }
                        for p in products
                    ]
                    
                    return ActionResult(
                        success=True,
                        action_type="inventory_query",
                        data=product_data,
                        message=f"Found {len(products)} products in {category_obj.name} category"
                    )
                else:
                    return ActionResult(
                        success=True,
                        action_type="inventory_query",
                        data=[],
                        message=f"No category found matching '{category}'"
                    )
            
            # General inventory overview
            else:
                total_products = session.query(Product).filter(Product.is_active == True).count()
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
                
                # Get some sample products
                sample_products = session.query(Product).filter(
                    Product.is_active == True
                ).order_by(Product.name).limit(20).all()
                
                overview_data = {
                    'total_products': total_products,
                    'low_stock_count': low_stock_count,
                    'out_of_stock_count': out_of_stock_count,
                    'sample_products': [
                        {
                            'sku': p.sku,
                            'name': p.name,
                            'current_stock': p.current_stock,
                            'stock_status': p.stock_status
                        }
                        for p in sample_products
                    ]
                }
                
                return ActionResult(
                    success=True,
                    action_type="inventory_overview",
                    data=overview_data,
                    message=f"Inventory overview: {total_products} total products"
                )
    
    def _handle_product_search(self, entities: Dict[str, Any]) -> ActionResult:
        """Handle product search queries."""
        with db_manager.get_session() as session:
            search_term = entities.get('product_name', '')
            category = entities.get('category')
            
            query = session.query(Product).filter(Product.is_active == True)
            
            if search_term:
                query = query.filter(
                    or_(
                        Product.name.ilike(f'%{search_term}%'),
                        Product.sku.ilike(f'%{search_term}%'),
                        Product.description.ilike(f'%{search_term}%')
                    )
                )
            
            if category:
                category_obj = session.query(Category).filter(
                    Category.name.ilike(f'%{category}%')
                ).first()
                if category_obj:
                    query = query.filter(Product.category_id == category_obj.id)
            
            products = query.limit(20).all()
            
            product_data = [
                {
                    'id': p.id,
                    'sku': p.sku,
                    'name': p.name,
                    'description': p.description,
                    'current_stock': p.current_stock,
                    'wholesale_price': float(p.wholesale_price),
                    'retail_price': float(p.retail_price) if p.retail_price else None,
                    'category': p.category.name,
                    'supplier': p.supplier.name,
                    'is_active': p.is_active
                }
                for p in products
            ]
            
            return ActionResult(
                success=True,
                action_type="product_search",
                data=product_data,
                message=f"Found {len(products)} products"
            )
    
    def _handle_inventory_management(self, entities: Dict[str, Any]) -> ActionResult:
        """Handle inventory management operations."""
        action = entities.get('action', '').lower()
        product_name = entities.get('product_name')
        quantity_str = entities.get('quantity')
        
        # Validate inputs
        if not action:
            return ActionResult(
                success=False,
                action_type="inventory_management",
                error="No action specified (add, remove, adjust, etc.)"
            )
        
        if not product_name:
            return ActionResult(
                success=False,
                action_type="inventory_management",
                error="No product specified"
            )
        
        try:
            quantity = int(quantity_str) if quantity_str else None
        except (ValueError, TypeError):
            return ActionResult(
                success=False,
                action_type="inventory_management",
                error=f"Invalid quantity: {quantity_str}"
            )
        
        if quantity is None:
            return ActionResult(
                success=False,
                action_type="inventory_management",
                error="No quantity specified"
            )
        
        try:
            # Execute inventory operation
            if action in ['add', 'increase', 'receive', 'restock']:
                result = self.inventory_manager.add_stock(
                    product_identifier=product_name,
                    quantity=quantity,
                    notes=f"Stock added via AI agent"
                )
            elif action in ['remove', 'decrease', 'sell', 'ship', 'lost', 'lose']:
                reason = 'DAMAGED' if action in ['lost', 'lose'] else 'OUTBOUND'
                result = self.inventory_manager.remove_stock(
                    product_identifier=product_name,
                    quantity=quantity,
                    reason=reason,
                    notes=f"Stock {action} via AI agent"
                )
            elif action in ['adjust', 'set', 'update']:
                result = self.inventory_manager.adjust_stock(
                    product_identifier=product_name,
                    new_quantity=quantity,
                    reason=f"Stock adjusted via AI agent"
                )
            else:
                return ActionResult(
                    success=False,
                    action_type="inventory_management",
                    error=f"Unknown action: {action}"
                )
            
            return ActionResult(
                success=result.get('success', False),
                action_type="inventory_management",
                data=result,
                message=result.get('message', ''),
                error=result.get('error') if not result.get('success') else None
            )
            
        except Exception as e:
            return ActionResult(
                success=False,
                action_type="inventory_management",
                error=f"Operation failed: {str(e)}"
            )
    
    def _handle_analytics(self, entities: Dict[str, Any]) -> ActionResult:
        """Handle analytics and business intelligence queries."""
        with db_manager.get_session() as session:
            # Get business analytics data
            total_products = session.query(Product).filter(Product.is_active == True).count()
            total_inventory_value = session.query(
                func.sum(Product.current_stock * Product.cost_price)
            ).filter(Product.is_active == True).scalar() or 0
            
            # Top categories by product count
            top_categories = session.query(
                Category.name,
                func.count(Product.id).label('product_count'),
                func.sum(Product.current_stock * Product.cost_price).label('category_value')
            ).join(Product).filter(Product.is_active == True).group_by(Category.name).order_by(
                func.count(Product.id).desc()
            ).limit(10).all()
            
            # Recent inventory movements
            recent_movements = session.query(InventoryMovement).order_by(
                InventoryMovement.created_at.desc()
            ).limit(10).all()
            
            analytics_data = {
                'total_products': total_products,
                'total_inventory_value': float(total_inventory_value),
                'top_categories': [
                    {
                        'name': cat.name,
                        'product_count': cat.product_count,
                        'inventory_value': float(cat.category_value or 0)
                    }
                    for cat in top_categories
                ],
                'recent_movements': [
                    {
                        'id': m.id,
                        'product_name': m.product.name,
                        'product_sku': m.product.sku,
                        'movement_type': m.movement_type,
                        'quantity': m.quantity,
                        'created_at': m.created_at.isoformat(),
                        'reference_number': m.reference_number
                    }
                    for m in recent_movements
                ]
            }
            
            return ActionResult(
                success=True,
                action_type="analytics",
                data=analytics_data,
                message="Business analytics data retrieved"
            )
    
    def _handle_supplier_query(self, entities: Dict[str, Any]) -> ActionResult:
        """Handle supplier queries."""
        with db_manager.get_session() as session:
            supplier_name = entities.get('supplier')
            
            if supplier_name:
                suppliers = session.query(Supplier).filter(
                    Supplier.name.ilike(f'%{supplier_name}%')
                ).limit(10).all()
            else:
                suppliers = session.query(Supplier).filter(
                    Supplier.is_active == True
                ).limit(10).all()
            
            supplier_data = [
                {
                    'id': s.id,
                    'name': s.name,
                    'contact_email': s.contact_email,
                    'contact_phone': s.contact_phone,
                    'payment_terms': s.payment_terms,
                    'is_active': s.is_active,
                    'product_count': len(s.products) if s.products else 0
                }
                for s in suppliers
            ]
            
            return ActionResult(
                success=True,
                action_type="supplier_query",
                data=supplier_data,
                message=f"Found {len(suppliers)} suppliers"
            )
    
    def _handle_price_query(self, entities: Dict[str, Any]) -> ActionResult:
        """Handle price queries."""
        with db_manager.get_session() as session:
            product_name = entities.get('product_name')
            
            if not product_name:
                return ActionResult(
                    success=False,
                    action_type="price_query",
                    error="No product specified for price query"
                )
            
            products = session.query(Product).filter(
                and_(
                    Product.is_active == True,
                    Product.name.ilike(f'%{product_name}%')
                )
            ).limit(10).all()
            
            if not products:
                return ActionResult(
                    success=True,
                    action_type="price_query",
                    data=[],
                    message=f"No products found matching '{product_name}'"
                )
            
            price_data = [
                {
                    'sku': p.sku,
                    'name': p.name,
                    'wholesale_price': float(p.wholesale_price),
                    'retail_price': float(p.retail_price) if p.retail_price else None,
                    'cost_price': float(p.cost_price) if p.cost_price else None,
                    'current_stock': p.current_stock
                }
                for p in products
            ]
            
            return ActionResult(
                success=True,
                action_type="price_query",
                data=price_data,
                message=f"Found pricing for {len(products)} products"
            )
    
    def _handle_low_stock_alert(self, entities: Dict[str, Any]) -> ActionResult:
        """Handle low stock alerts."""
        with db_manager.get_session() as session:
            # Get low stock products
            low_stock_products = session.query(Product).filter(
                and_(
                    Product.is_active == True,
                    Product.current_stock <= Product.minimum_stock
                )
            ).order_by(Product.current_stock.asc()).limit(50).all()
            
            # Get out of stock products
            out_of_stock_products = session.query(Product).filter(
                and_(
                    Product.is_active == True,
                    Product.current_stock <= 0
                )
            ).limit(20).all()
            
            low_stock_data = [
                {
                    'sku': p.sku,
                    'name': p.name,
                    'current_stock': p.current_stock,
                    'minimum_stock': p.minimum_stock,
                    'category': p.category.name,
                    'supplier': p.supplier.name,
                    'stock_status': p.stock_status
                }
                for p in low_stock_products
            ]
            
            out_of_stock_data = [
                {
                    'sku': p.sku,
                    'name': p.name,
                    'current_stock': p.current_stock,
                    'category': p.category.name,
                    'supplier': p.supplier.name
                }
                for p in out_of_stock_products
            ]
            
            alert_data = {
                'low_stock_products': low_stock_data,
                'out_of_stock_products': out_of_stock_data,
                'low_stock_count': len(low_stock_data),
                'out_of_stock_count': len(out_of_stock_data)
            }
            
            return ActionResult(
                success=True,
                action_type="low_stock_alert",
                data=alert_data,
                message=f"Found {len(low_stock_data)} low stock and {len(out_of_stock_data)} out of stock products"
            )
    
    def _handle_inventory_history(self, entities: Dict[str, Any]) -> ActionResult:
        """Handle inventory history queries."""
        with db_manager.get_session() as session:
            product_name = entities.get('product_name')
            
            if not product_name:
                return ActionResult(
                    success=False,
                    action_type="inventory_history",
                    error="No product specified for history query"
                )
            
            # Find the product
            products = session.query(Product).filter(
                and_(
                    Product.is_active == True,
                    Product.name.ilike(f'%{product_name}%')
                )
            ).limit(5).all()
            
            if not products:
                return ActionResult(
                    success=True,
                    action_type="inventory_history",
                    data=[],
                    message=f"No products found matching '{product_name}'"
                )
            
            history_data = []
            for product in products:
                # Get recent inventory movements for this product
                movements = session.query(InventoryMovement).filter(
                    InventoryMovement.product_id == product.id
                ).order_by(InventoryMovement.created_at.desc()).limit(10).all()
                
                last_update = None
                if movements:
                    last_update = movements[0].created_at
                
                recent_movements = [
                    {
                        'movement_type': m.movement_type,
                        'quantity': m.quantity,
                        'created_at': m.created_at.isoformat(),
                        'reference_number': m.reference_number
                    }
                    for m in movements[:5]  # Show last 5 movements
                ]
                
                product_history = {
                    'sku': product.sku,
                    'name': product.name,
                    'current_stock': product.current_stock,
                    'last_updated': last_update.isoformat() if last_update else None,
                    'last_update_days_ago': (datetime.now() - last_update).days if last_update else None,
                    'recent_movements': recent_movements,
                    'total_movements': len(movements)
                }
                history_data.append(product_history)
            
            return ActionResult(
                success=True,
                action_type="inventory_history",
                data=history_data,
                message=f"Found inventory history for {len(history_data)} products"
            )
    
    def _handle_help_capabilities(self, entities: Dict[str, Any]) -> ActionResult:
        """Handle help and capabilities queries."""
        capabilities = {
            "inventory_operations": {
                "description": "Manage your inventory with natural language",
                "examples": [
                    "How much stock of gaming keyboard do we have?",
                    "Add 50 units to laptop stand",
                    "Remove 10 brake pads from inventory",
                    "Adjust wireless mouse stock to 100 units"
                ]
            },
            "product_search": {
                "description": "Find and browse your product catalog",
                "examples": [
                    "Show me all electronics products",
                    "Find products with 'wireless' in the name",
                    "Search for products from Samsung supplier"
                ]
            },
            "pricing_information": {
                "description": "Get pricing details for products",
                "examples": [
                    "What's the price of gaming keyboard?",
                    "Show pricing for all laptop products",
                    "What's the wholesale price of phone charger?"
                ]
            },
            "inventory_history": {
                "description": "Check when products were last updated or modified",
                "examples": [
                    "What's the last time we updated brake pads?",
                    "When did we last modify gaming keyboard stock?",
                    "Show recent inventory movements for wireless mouse"
                ]
            },
            "analytics_reporting": {
                "description": "Get business insights and analytics",
                "examples": [
                    "Show me business analytics",
                    "What's our total inventory value?",
                    "How many products do we have in total?"
                ]
            },
            "stock_alerts": {
                "description": "Check for low stock and out-of-stock products",
                "examples": [
                    "Show me all low stock products",
                    "Which products are out of stock?",
                    "Alert me about inventory issues"
                ]
            },
            "supplier_information": {
                "description": "Get information about your suppliers",
                "examples": [
                    "Show me all active suppliers",
                    "Find supplier information for TechCorp",
                    "Which suppliers do we work with?"
                ]
            },
            "contextual_conversations": {
                "description": "Have natural follow-up conversations",
                "examples": [
                    "User: 'How much stock of gaming keyboard?'",
                    "Agent: [Shows stock info]",
                    "User: 'What about its price?' (Agent understands 'its' refers to gaming keyboard)",
                    "User: 'Remove 2 units of it' (Agent applies to gaming keyboard)"
                ]
            }
        }
        
        return ActionResult(
            success=True,
            action_type="help_capabilities",
            data=capabilities,
            message="Here are my capabilities and what you can ask me"
        )