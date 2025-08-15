#!/usr/bin/env python3
"""
Test script to verify the e-commerce competitor monitoring setup
"""

import sys
import os

def test_imports():
    """Test that all modules can be imported successfully."""
    print("Testing imports...")
    
    try:
        from config.settings import settings
        print("✓ Settings imported successfully")
    except Exception as e:
        print(f"✗ Error importing settings: {e}")
        return False
    
    try:
        from core.database.manager import DatabaseManager
        print("✓ Database manager imported successfully")
    except Exception as e:
        print(f"✗ Error importing database manager: {e}")
        return False
    
    try:
        from core.scrapers import get_scraper_for_url
        print("✓ Scrapers imported successfully")
    except Exception as e:
        print(f"✗ Error importing scrapers: {e}")
        return False
    
    try:
        from core.alerts.alert_manager import AlertManager
        print("✓ Alert manager imported successfully")
    except Exception as e:
        print(f"✗ Error importing alert manager: {e}")
        return False
    
    try:
        from core.monitor import CompetitorMonitor
        print("✓ Monitor imported successfully")
    except Exception as e:
        print(f"✗ Error importing monitor: {e}")
        return False
    
    return True

def test_database():
    """Test database operations."""
    print("\nTesting database operations...")
    
    try:
        from core.database.manager import DatabaseManager
        
        # Create database manager
        db = DatabaseManager()
        
        # Create tables
        db.create_tables()
        print("✓ Database tables created successfully")
        
        # Test adding a competitor
        competitor_data = {
            'name': 'Test Competitor',
            'domain': 'test.com',
            'base_url': 'https://test.com'
        }
        
        competitor = db.add_competitor(competitor_data)
        print(f"✓ Added test competitor: {competitor.name}")
        
        # Test getting competitors
        competitors = db.get_competitors()
        print(f"✓ Retrieved {len(competitors)} competitors")
        
        return True
        
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

def test_scrapers():
    """Test scraper functionality."""
    print("\nTesting scrapers...")
    
    try:
        from core.scrapers import get_scraper_for_url
        
        # Test getting scraper for Amazon URL
        amazon_url = "https://www.amazon.com/test-product"
        scraper = get_scraper_for_url(amazon_url)
        print(f"✓ Got scraper for Amazon URL: {scraper.get_platform_name()}")
        
        return True
        
    except Exception as e:
        print(f"✗ Scraper test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing E-commerce Competitor Monitoring Setup")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed. Please check your installation.")
        return False
    
    # Test database
    if not test_database():
        print("\n❌ Database tests failed. Please check your database configuration.")
        return False
    
    # Test scrapers
    if not test_scrapers():
        print("\n❌ Scraper tests failed. Please check your scraper configuration.")
        return False
    
    print("\n✅ All tests passed! Your setup is ready to use.")
    print("\nNext steps:")
    print("1. Configure your .env file with your settings")
    print("2. Run 'python main.py' to start the monitoring agent")
    print("3. Run 'python dashboard.py' to start the web dashboard")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)