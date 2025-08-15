#!/usr/bin/env python3
"""
Add sample products script
Adds sample products to monitor for testing the system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database.manager import DatabaseManager

def add_sample_products():
    """Add sample products to monitor."""
    print("Adding sample products...")
    
    # Create database manager
    db = DatabaseManager()
    
    # Sample products (using real Amazon URLs for testing)
    sample_products = [
        {
            'name': 'Echo Dot (4th Gen) | Smart speaker with Alexa',
            'url': 'https://www.amazon.com/Echo-Dot-4th-Gen-Charcoal/dp/B07XJ8C8F5/',
            'competitor': 'Amazon',
            'category': 'Electronics',
            'target_price': 49.99
        },
        {
            'name': 'Fire TV Stick 4K Max streaming device',
            'url': 'https://www.amazon.com/Fire-TV-Stick-4K-Max/dp/B08MQZXN1X/',
            'competitor': 'Amazon',
            'category': 'Electronics',
            'target_price': 54.99
        },
        {
            'name': 'Kindle Paperwhite (8 GB)',
            'url': 'https://www.amazon.com/All-new-Kindle-Paperwhite-8GB/dp/B08N36XNTT/',
            'competitor': 'Amazon',
            'category': 'Electronics',
            'target_price': 139.99
        }
    ]
    
    for product_data in sample_products:
        try:
            # Check if product already exists
            existing_products = db.get_products(active_only=False)
            if not any(p.url == product_data['url'] for p in existing_products):
                product = db.add_product(product_data)
                print(f"✓ Added product: {product.name}")
                
                # Set up default alerts
                db.add_alert({
                    'product_id': product.id,
                    'alert_type': 'price_drop',
                    'threshold': 5.0  # 5% price drop
                })
                db.add_alert({
                    'product_id': product.id,
                    'alert_type': 'stock_change',
                    'threshold': None
                })
                print(f"  ✓ Set up default alerts for {product.name}")
            else:
                print(f"⚠ Product already exists: {product_data['name']}")
        except Exception as e:
            print(f"✗ Error adding product {product_data['name']}: {e}")
    
    print("\nSample products added!")
    print(f"Total products in database: {len(db.get_products())}")

if __name__ == "__main__":
    add_sample_products()