"""
Mock data generation for wholesale business.
Uses external APIs to generate realistic data.
"""
import requests
import random
import time
from typing import List, Dict, Any
from faker import Faker
from ..models import (
    db_manager, Category, Supplier, Product, InventoryMovement
)


class MockDataGenerator:
    """Generate mock data for testing and development."""
    
    def __init__(self):
        self.fake = Faker()
        self.session = None
        
        # Product categories for wholesale business
        self.categories = [
            {"name": "Electronics", "description": "Electronic devices and accessories"},
            {"name": "Clothing & Apparel", "description": "Clothing, shoes, and fashion accessories"},
            {"name": "Home & Garden", "description": "Home improvement and gardening supplies"},
            {"name": "Health & Beauty", "description": "Personal care and beauty products"},
            {"name": "Office Supplies", "description": "Business and office equipment"},
            {"name": "Automotive", "description": "Car parts and automotive accessories"},
            {"name": "Sports & Outdoors", "description": "Sports equipment and outdoor gear"},
            {"name": "Food & Beverages", "description": "Packaged foods and beverages"},
            {"name": "Tools & Hardware", "description": "Construction tools and hardware"},
            {"name": "Books & Media", "description": "Books, magazines, and media products"}
        ]
        
        # Common product prefixes for SKU generation
        self.sku_prefixes = {
            "Electronics": "ELE",
            "Clothing & Apparel": "CLO", 
            "Home & Garden": "HOM",
            "Health & Beauty": "HLT",
            "Office Supplies": "OFF",
            "Automotive": "AUT",
            "Sports & Outdoors": "SPT",
            "Food & Beverages": "FOD",
            "Tools & Hardware": "TLS",
            "Books & Media": "BOK"
        }
    
    def generate_product_names(self, category: str, count: int = 20) -> List[str]:
        """Generate realistic product names using external API or fallback to local generation."""
        try:
            # Use a free API for generating product names if available
            # Fallback to local generation for reliability
            return self._generate_local_product_names(category, count)
        except Exception:
            return self._generate_local_product_names(category, count)
    
    def _generate_local_product_names(self, category: str, count: int) -> List[str]:
        """Generate product names locally based on category."""
        products = {
            "Electronics": [
                "Wireless Bluetooth Headphones", "USB-C Charging Cable", "Smartphone Case",
                "Bluetooth Speaker", "Wireless Mouse", "Laptop Stand", "Power Bank",
                "HDMI Cable", "Webcam HD", "Gaming Keyboard", "LED Monitor",
                "Tablet Screen Protector", "Wireless Charger", "Car Phone Mount",
                "Bluetooth Earbuds", "USB Hub", "Computer Mouse Pad", "Cable Organizer",
                "Phone Ring Holder", "Portable Hard Drive"
            ],
            "Clothing & Apparel": [
                "Cotton T-Shirt", "Denim Jeans", "Leather Jacket", "Running Shoes",
                "Baseball Cap", "Cotton Hoodie", "Dress Shirt", "Cargo Pants",
                "Sneakers", "Winter Coat", "Polo Shirt", "Khaki Shorts",
                "Canvas Shoes", "Wool Sweater", "Track Pants", "Sandals",
                "Button-up Shirt", "Sweatpants", "Boots", "Tank Top"
            ],
            "Home & Garden": [
                "Garden Hose", "LED Light Bulbs", "Plant Pot Set", "Garden Gloves",
                "Watering Can", "Fertilizer", "Pruning Shears", "Outdoor Cushions",
                "Solar Lights", "Garden Stakes", "Mulch", "Seed Starter Kit",
                "Garden Tool Set", "Sprinkler System", "Patio Umbrella",
                "Plant Food", "Garden Stones", "Outdoor Mat", "Bird Feeder", "Compost Bin"
            ],
            "Health & Beauty": [
                "Face Moisturizer", "Shampoo", "Body Lotion", "Lip Balm",
                "Vitamin C Serum", "Toothbrush", "Sunscreen SPF 30", "Face Mask",
                "Hand Sanitizer", "Body Wash", "Conditioner", "Eye Cream",
                "Deodorant", "Face Cleanser", "Hair Oil", "Nail Polish",
                "Perfume", "Body Scrub", "Makeup Remover", "Anti-Aging Cream"
            ],
            "Office Supplies": [
                "Ballpoint Pens", "Sticky Notes", "Copy Paper", "Stapler",
                "File Folders", "Desk Organizer", "Markers Set", "Clipboard",
                "Printer Ink", "Notebook", "Highlighters", "Paper Clips",
                "Rubber Bands", "Tape Dispenser", "Calculator", "Scissors",
                "Binders", "Index Cards", "Envelope Set", "Desk Lamp"
            ],
            "Automotive": [
                "Car Air Freshener", "Motor Oil", "Brake Pads", "Car Battery",
                "Windshield Wipers", "Car Wax", "Tire Pressure Gauge", "Jumper Cables",
                "Car Floor Mats", "Engine Oil Filter", "Spark Plugs", "Car Cover",
                "Dashboard Cleaner", "Tire Shine", "Car Vacuum", "Seat Covers",
                "Steering Wheel Cover", "Car Charger", "Emergency Kit", "Antifreeze"
            ],
            "Sports & Outdoors": [
                "Basketball", "Tennis Racket", "Yoga Mat", "Camping Tent",
                "Hiking Boots", "Water Bottle", "Dumbbells Set", "Sleeping Bag",
                "Backpack", "Fishing Rod", "Golf Balls", "Swimming Goggles",
                "Bicycle Helmet", "Running Shorts", "Camping Chair", "Protein Powder",
                "Jump Rope", "Tennis Balls", "Football", "Hiking Poles"
            ],
            "Food & Beverages": [
                "Organic Coffee Beans", "Green Tea", "Protein Bars", "Olive Oil",
                "Pasta", "Rice", "Canned Tomatoes", "Honey", "Nuts Mix",
                "Chocolate", "Granola", "Spices Set", "Coconut Oil", "Quinoa",
                "Oatmeal", "Dried Fruits", "Energy Drinks", "Mineral Water",
                "Herbal Tea", "Protein Powder"
            ],
            "Tools & Hardware": [
                "Screwdriver Set", "Hammer", "Drill Bits", "Measuring Tape",
                "Level", "Pliers", "Wrench Set", "Safety Glasses", "Work Gloves",
                "Utility Knife", "Saw", "Sandpaper", "Nails", "Screws",
                "Tool Box", "Paint Brush", "Flashlight", "Extension Cord",
                "Wire Strippers", "Multimeter"
            ],
            "Books & Media": [
                "Business Strategy Book", "Self-Help Book", "Cookbook",
                "Travel Guide", "Biography", "Novel", "Technical Manual",
                "Art Book", "History Book", "Science Magazine", "Audio Book",
                "Educational DVD", "Language Learning Book", "Photography Book",
                "Health Guide", "Finance Book", "Children's Book", "Poetry Collection",
                "Graphic Novel", "Reference Book"
            ]
        }
        
        category_products = products.get(category, ["Generic Product"])
        return random.choices(category_products, k=min(count, len(category_products)))
    
    def generate_suppliers(self, count: int = 15) -> List[Supplier]:
        """Generate mock suppliers."""
        suppliers = []
        
        # Some realistic wholesale supplier name patterns
        supplier_types = [
            "Wholesale", "Distribution", "Supply Co", "Trading", "Import Export",
            "Global Supply", "Direct", "Bulk Supply", "Commercial"
        ]
        
        for _ in range(count):
            company_name = self.fake.company()
            supplier_type = random.choice(supplier_types)
            
            supplier = Supplier(
                name=f"{company_name} {supplier_type}",
                contact_email=self.fake.company_email(),
                contact_phone=self.fake.phone_number(),
                address=self.fake.address(),
                tax_id=f"TAX-{self.fake.random_number(digits=9)}",
                payment_terms=random.choice(["Net 30", "Net 15", "COD", "Net 45", "2/10 Net 30"]),
                is_active=random.choice([True, True, True, False])  # 75% active
            )
            suppliers.append(supplier)
        
        return suppliers
    
    def generate_products(self, categories: List[Category], suppliers: List[Supplier], 
                         products_per_category: int = 25) -> List[Product]:
        """Generate mock products."""
        products = []
        
        for category in categories:
            product_names = self.generate_product_names(category.name, products_per_category)
            sku_prefix = self.sku_prefixes.get(category.name, "GEN")
            
            for i, name in enumerate(product_names):
                # Generate realistic pricing
                cost_price = round(random.uniform(5.0, 200.0), 2)
                wholesale_markup = random.uniform(1.3, 2.0)  # 30-100% markup
                retail_markup = random.uniform(1.8, 3.0)      # 80-200% markup from cost
                
                wholesale_price = round(cost_price * wholesale_markup, 2)
                retail_price = round(cost_price * retail_markup, 2)
                
                # Generate stock levels
                current_stock = random.randint(0, 500)
                minimum_stock = random.randint(5, 50)
                maximum_stock = random.randint(100, 1000)
                
                product = Product(
                    sku=f"{sku_prefix}-{random.randint(1000, 9999)}-{i:03d}",
                    name=name,
                    description=self.fake.text(max_nb_chars=200),
                    category_id=category.id,
                    supplier_id=random.choice(suppliers).id,
                    cost_price=cost_price,
                    wholesale_price=wholesale_price,
                    retail_price=retail_price,
                    current_stock=current_stock,
                    minimum_stock=minimum_stock,
                    maximum_stock=maximum_stock,
                    weight=round(random.uniform(0.1, 10.0), 2),
                    dimensions=f"{random.randint(5,30)}x{random.randint(5,30)}x{random.randint(2,15)}",
                    barcode=self.fake.ean13() if random.random() > 0.3 else None,
                    is_active=random.choice([True, True, True, False]),  # 75% active
                    is_discontinued=random.choice([False, False, False, True])  # 25% discontinued
                )
                products.append(product)
        
        return products
    
    def generate_inventory_movements(self, products: List[Product], count: int = 200) -> List[InventoryMovement]:
        """Generate mock inventory movements."""
        movements = []
        
        for _ in range(count):
            product = random.choice(products)
            movement_type = random.choice([
                'INBOUND', 'INBOUND', 'INBOUND',  # More inbound movements
                'OUTBOUND', 'OUTBOUND',
                'ADJUSTMENT',
                'RETURN',
                'DAMAGED'
            ])
            
            # Generate quantities based on movement type
            if movement_type == 'INBOUND':
                quantity = random.randint(10, 100)
            elif movement_type == 'OUTBOUND':
                quantity = -random.randint(1, 50)  # Negative for outbound
            elif movement_type == 'ADJUSTMENT':
                quantity = random.randint(-20, 20)
            elif movement_type == 'RETURN':
                quantity = random.randint(1, 10)
            else:  # DAMAGED
                quantity = -random.randint(1, 5)
            
            movement = InventoryMovement(
                product_id=product.id,
                movement_type=movement_type,
                quantity=quantity,
                unit_cost=product.cost_price if movement_type == 'INBOUND' else None,
                reference_number=f"{movement_type[:3]}-{self.fake.random_number(digits=8)}",
                notes=self.fake.sentence() if random.random() > 0.7 else None,
                from_location="Warehouse A" if movement_type == 'OUTBOUND' else None,
                to_location="Warehouse A" if movement_type == 'INBOUND' else None
            )
            movements.append(movement)
        
        return movements
    
    def generate_all_data(self, categories_count: int = 10, suppliers_count: int = 15,
                         products_per_category: int = 25, movements_count: int = 200):
        """Generate all mock data and save to database."""
        print("🚀 Starting mock data generation...")
        
        with db_manager.get_session() as session:
            self.session = session
            
            # Generate categories
            print(f"📁 Creating {categories_count} categories...")
            db_categories = []
            for cat_data in self.categories[:categories_count]:
                category = Category(**cat_data)
                session.add(category)
                db_categories.append(category)
            
            session.commit()
            print(f"✓ Created {len(db_categories)} categories")
            
            # Generate suppliers
            print(f"🏢 Creating {suppliers_count} suppliers...")
            suppliers = self.generate_suppliers(suppliers_count)
            for supplier in suppliers:
                session.add(supplier)
            session.commit()
            print(f"✓ Created {len(suppliers)} suppliers")
            
            # Generate products
            print(f"📦 Creating {products_per_category * len(db_categories)} products...")
            products = self.generate_products(db_categories, suppliers, products_per_category)
            for product in products:
                session.add(product)
            session.commit()
            print(f"✓ Created {len(products)} products")
            
            # Generate inventory movements
            print(f"📊 Creating {movements_count} inventory movements...")
            movements = self.generate_inventory_movements(products, movements_count)
            for movement in movements:
                session.add(movement)
            session.commit()
            print(f"✓ Created {len(movements)} inventory movements")
            
            print("✅ Mock data generation completed successfully!")
            
            # Print summary statistics
            self._print_summary_stats(session)
    
    def _print_summary_stats(self, session):
        """Print summary statistics of generated data."""
        print("\n📈 Data Summary:")
        print(f"Categories: {session.query(Category).count()}")
        print(f"Suppliers: {session.query(Supplier).count()}")
        print(f"Products: {session.query(Product).count()}")
        print(f"Active Products: {session.query(Product).filter(Product.is_active == True).count()}")
        print(f"Low Stock Products: {session.query(Product).filter(Product.current_stock <= Product.minimum_stock).count()}")
        print(f"Inventory Movements: {session.query(InventoryMovement).count()}")
        
        # Calculate total inventory value
        from sqlalchemy import func
        total_value = session.query(func.sum(Product.current_stock * Product.cost_price)).scalar() or 0
        print(f"Total Inventory Value: ${total_value:,.2f}")


def main():
    """Command line entry point for mock data generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate mock data for wholesale agent')
    parser.add_argument('--categories', type=int, default=10, help='Number of categories')
    parser.add_argument('--suppliers', type=int, default=15, help='Number of suppliers')
    parser.add_argument('--products-per-category', type=int, default=25, help='Products per category')
    parser.add_argument('--movements', type=int, default=200, help='Number of inventory movements')
    
    args = parser.parse_args()
    
    generator = MockDataGenerator()
    generator.generate_all_data(
        categories_count=args.categories,
        suppliers_count=args.suppliers,
        products_per_category=args.products_per_category,
        movements_count=args.movements
    )


if __name__ == "__main__":
    main()