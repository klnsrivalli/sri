#!/usr/bin/env python3
"""
Database initialization script
Creates tables and adds sample data for the competitor monitoring system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database.manager import DatabaseManager
from core.database.models import Competitor
import json

def init_database():
    """Initialize the database with tables and sample data."""
    print("Initializing database...")
    
    # Create database manager
    db = DatabaseManager()
    
    # Create tables
    print("Creating database tables...")
    db.create_tables()
    print("✓ Database tables created successfully")
    
    # Add sample competitors
    print("Adding sample competitors...")
    sample_competitors = [
        {
            'name': 'Amazon',
            'domain': 'amazon.com',
            'base_url': 'https://www.amazon.com',
            'scraper_config': json.dumps({
                'selectors': {
                    'title': ['#productTitle'],
                    'price': ['.a-price-whole', '.a-price .a-offscreen'],
                    'rating': ['.a-icon-alt'],
                    'availability': ['#availability']
                }
            })
        },
        {
            'name': 'eBay',
            'domain': 'ebay.com',
            'base_url': 'https://www.ebay.com',
            'scraper_config': json.dumps({
                'selectors': {
                    'title': ['.x-item-title__mainTitle'],
                    'price': ['.x-price-primary'],
                    'rating': ['.x-star-rating'],
                    'availability': ['.x-item-condition']
                }
            })
        },
        {
            'name': 'Walmart',
            'domain': 'walmart.com',
            'base_url': 'https://www.walmart.com',
            'scraper_config': json.dumps({
                'selectors': {
                    'title': ['.prod-ProductTitle'],
                    'price': ['.price-characteristic'],
                    'rating': ['.stars-container'],
                    'availability': ['.prod-ProductOffer']
                }
            })
        }
    ]
    
    for competitor_data in sample_competitors:
        try:
            existing = db.get_competitors()
            if not any(c.name == competitor_data['name'] for c in existing):
                db.add_competitor(competitor_data)
                print(f"✓ Added competitor: {competitor_data['name']}")
            else:
                print(f"⚠ Competitor already exists: {competitor_data['name']}")
        except Exception as e:
            print(f"✗ Error adding competitor {competitor_data['name']}: {e}")
    
    print("\nDatabase initialization completed!")
    print("\nNext steps:")
    print("1. Copy .env.example to .env and configure your settings")
    print("2. Run 'python main.py' to start the monitoring agent")
    print("3. Run 'python dashboard.py' to start the web dashboard")
    print("4. Add products to monitor via the API or dashboard")

if __name__ == "__main__":
    init_database()