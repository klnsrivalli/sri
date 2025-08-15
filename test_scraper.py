#!/usr/bin/env python3
"""
Test script for the e-commerce competitor scraper
"""

import sys
import time
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from scraper import CompetitorScraper
from config import COMPETITOR_CONFIGS

def test_scraper():
    """Test the scraper functionality"""
    print("🧪 Testing E-commerce Competitor Scraper")
    print("=" * 50)
    
    # Test each configured competitor
    for competitor_name in COMPETITOR_CONFIGS.keys():
        print(f"\n📊 Testing {competitor_name.upper()} scraper...")
        
        try:
            # Create scraper instance
            scraper = CompetitorScraper(competitor_name)
            print(f"✅ {competitor_name} scraper initialized successfully")
            
            # Test search functionality
            print(f"🔍 Testing search functionality...")
            search_results = scraper.search_products("laptop", max_results=3)
            
            if search_results:
                print(f"✅ Found {len(search_results)} products")
                for i, product in enumerate(search_results[:2], 1):
                    print(f"   {i}. {product.get('title', 'N/A')} - ${product.get('price', 'N/A')}")
            else:
                print("⚠️  No search results found")
            
            # Test product details if we have a URL
            if search_results and search_results[0].get('url'):
                print(f"📋 Testing product details...")
                product_url = search_results[0]['url']
                details = scraper.get_product_details(product_url)
                
                if details:
                    print(f"✅ Product details retrieved successfully")
                    print(f"   Title: {details.get('title', 'N/A')}")
                    print(f"   Price: ${details.get('price', 'N/A')}")
                    print(f"   Available: {details.get('is_available', 'N/A')}")
                else:
                    print("⚠️  Could not retrieve product details")
            
            print(f"✅ {competitor_name} tests completed successfully")
            
        except Exception as e:
            print(f"❌ Error testing {competitor_name}: {e}")
        
        # Add delay between tests
        time.sleep(2)
    
    print("\n" + "=" * 50)
    print("🎉 Scraper testing completed!")

def test_web_scraping():
    """Test basic web scraping functionality"""
    print("\n🌐 Testing basic web scraping...")
    
    try:
        from scraper import WebScraper
        
        scraper = WebScraper()
        
        # Test with a simple website
        test_url = "https://httpbin.org/html"
        print(f"Testing with {test_url}...")
        
        soup = scraper.scrape_with_requests(test_url)
        if soup:
            print("✅ Basic web scraping successful")
            title = soup.find('title')
            if title:
                print(f"   Page title: {title.get_text()}")
        else:
            print("❌ Basic web scraping failed")
    
    except Exception as e:
        print(f"❌ Error in basic web scraping test: {e}")

def test_selenium():
    """Test Selenium functionality"""
    print("\n🤖 Testing Selenium functionality...")
    
    try:
        from scraper import WebScraper
        
        scraper = WebScraper()
        
        # Test Selenium with a simple website
        test_url = "https://httpbin.org/html"
        print(f"Testing Selenium with {test_url}...")
        
        soup = scraper.scrape_with_selenium(test_url)
        if soup:
            print("✅ Selenium scraping successful")
            title = soup.find('title')
            if title:
                print(f"   Page title: {title.get_text()}")
        else:
            print("❌ Selenium scraping failed")
    
    except Exception as e:
        print(f"❌ Error in Selenium test: {e}")

if __name__ == "__main__":
    print("🚀 Starting E-commerce Competitor Scraper Tests")
    
    # Test basic functionality
    test_web_scraping()
    test_selenium()
    
    # Test competitor scrapers
    test_scraper()
    
    print("\n✨ All tests completed!")