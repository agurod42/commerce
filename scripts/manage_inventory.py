#!/usr/bin/env python3
"""
Direct inventory management script for wholesale agent.
"""
import sys
import argparse
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wholesale_agent.core.inventory_manager import InventoryManager
from wholesale_agent.utils.logger import setup_logger


def print_result(result: dict):
    """Print operation result in a formatted way."""
    if result['success']:
        print(f"✅ {result['message']}")
        if 'product' in result:
            product = result['product']
            if 'old_stock' in product and 'new_stock' in product:
                print(f"   Stock: {product['old_stock']} → {product['new_stock']} units")
    else:
        print(f"❌ Error: {result['error']}")


def main():
    """Main CLI for inventory management."""
    parser = argparse.ArgumentParser(description='Manage wholesale inventory directly')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add stock command
    add_parser = subparsers.add_parser('add', help='Add stock to a product')
    add_parser.add_argument('product', help='Product SKU or name')
    add_parser.add_argument('quantity', type=int, help='Quantity to add')
    add_parser.add_argument('--cost', type=float, help='Cost per unit')
    add_parser.add_argument('--reference', help='Reference number (PO, etc.)')
    add_parser.add_argument('--notes', help='Additional notes')
    
    # Remove stock command
    remove_parser = subparsers.add_parser('remove', help='Remove stock from a product')
    remove_parser.add_argument('product', help='Product SKU or name')
    remove_parser.add_argument('quantity', type=int, help='Quantity to remove')
    remove_parser.add_argument('--reason', choices=['OUTBOUND', 'DAMAGED', 'ADJUSTMENT'], 
                              default='OUTBOUND', help='Reason for removal')
    remove_parser.add_argument('--reference', help='Reference number')
    remove_parser.add_argument('--notes', help='Additional notes')
    
    # Adjust stock command
    adjust_parser = subparsers.add_parser('adjust', help='Set stock to specific quantity')
    adjust_parser.add_argument('product', help='Product SKU or name')
    adjust_parser.add_argument('quantity', type=int, help='New stock quantity')
    adjust_parser.add_argument('--reason', help='Reason for adjustment')
    adjust_parser.add_argument('--reference', help='Reference number')
    
    # Create product command
    create_parser = subparsers.add_parser('create', help='Create a new product')
    create_parser.add_argument('sku', help='Product SKU')
    create_parser.add_argument('name', help='Product name')
    create_parser.add_argument('category', help='Category name')
    create_parser.add_argument('supplier', help='Supplier name')
    create_parser.add_argument('cost_price', type=float, help='Cost price per unit')
    create_parser.add_argument('wholesale_price', type=float, help='Wholesale price per unit')
    create_parser.add_argument('retail_price', type=float, help='Retail price per unit')
    create_parser.add_argument('--initial-stock', type=int, default=0, help='Initial stock quantity')
    create_parser.add_argument('--min-stock', type=int, default=10, help='Minimum stock level')
    create_parser.add_argument('--max-stock', type=int, default=1000, help='Maximum stock level')
    create_parser.add_argument('--description', help='Product description')
    
    # Update prices command
    price_parser = subparsers.add_parser('price', help='Update product prices')
    price_parser.add_argument('product', help='Product SKU or name')
    price_parser.add_argument('--cost', type=float, help='New cost price')
    price_parser.add_argument('--wholesale', type=float, help='New wholesale price')
    price_parser.add_argument('--retail', type=float, help='New retail price')
    
    # Stock movements command
    moves_parser = subparsers.add_parser('movements', help='Show stock movements')
    moves_parser.add_argument('product', help='Product SKU or name')
    moves_parser.add_argument('--limit', type=int, default=10, help='Number of movements to show')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize inventory manager
    logger = setup_logger('inventory_cli', 'INFO')
    manager = InventoryManager()
    
    try:
        if args.command == 'add':
            result = manager.add_stock(
                product_identifier=args.product,
                quantity=args.quantity,
                cost_price=args.cost,
                reference=args.reference,
                notes=args.notes
            )
            print_result(result)
            
        elif args.command == 'remove':
            result = manager.remove_stock(
                product_identifier=args.product,
                quantity=args.quantity,
                reason=args.reason,
                reference=args.reference,
                notes=args.notes
            )
            print_result(result)
            
        elif args.command == 'adjust':
            result = manager.adjust_stock(
                product_identifier=args.product,
                new_quantity=args.quantity,
                reason=args.reason,
                reference=args.reference
            )
            print_result(result)
            
        elif args.command == 'create':
            result = manager.create_product(
                sku=args.sku,
                name=args.name,
                category_name=args.category,
                supplier_name=args.supplier,
                cost_price=args.cost_price,
                wholesale_price=args.wholesale_price,
                retail_price=args.retail_price,
                initial_stock=args.initial_stock,
                minimum_stock=args.min_stock,
                maximum_stock=args.max_stock,
                description=args.description
            )
            print_result(result)
            
        elif args.command == 'price':
            result = manager.update_product_prices(
                product_identifier=args.product,
                cost_price=args.cost,
                wholesale_price=args.wholesale,
                retail_price=args.retail
            )
            print_result(result)
            
        elif args.command == 'movements':
            result = manager.get_stock_movements(
                product_identifier=args.product,
                limit=args.limit
            )
            
            if result['success']:
                product = result['product']
                print(f"📦 Stock movements for {product['name']} (SKU: {product['sku']})")
                print(f"   Current stock: {product['current_stock']} units")
                print(f"   Recent movements:")
                
                for movement in result['movements']:
                    symbol = "📈" if movement['quantity'] > 0 else "📉"
                    print(f"   {symbol} {movement['date']}: {movement['quantity']:+d} units ({movement['type']})")
                    if movement['reference']:
                        print(f"       Ref: {movement['reference']}")
                    if movement['notes']:
                        print(f"       Notes: {movement['notes']}")
            else:
                print_result(result)
                
    except KeyboardInterrupt:
        print("\n👋 Cancelled")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logger.error(f"CLI error: {e}", exc_info=True)


if __name__ == "__main__":
    main()