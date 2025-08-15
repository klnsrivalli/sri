#!/usr/bin/env python3
"""
Example usage of the E-commerce Competitor Monitoring Agent

This script demonstrates how to set up monitoring for multiple competitors
and products programmatically.
"""

import time
from monitor import price_monitor
from visualizations import viz_engine
from notifications import NotificationManager

def setup_example_monitoring():
    """Set up example competitors and products for monitoring"""
    
    print("🚀 Setting up example competitor monitoring...")
    
    # Example 1: Add Amazon as a competitor
    amazon_selectors = {
        "price": ".a-price .a-offscreen, .a-price-whole",
        "title": "#productTitle",
        "availability": "#availability span",
        "rating": ".a-icon-alt, .a-icon.a-icon-star .a-icon-alt",
        "image": "#landingImage, .a-dynamic-image"
    }
    
    try:
        amazon_id = price_monitor.add_competitor(
            "Amazon", 
            "https://www.amazon.com", 
            amazon_selectors
        )
        print(f"✅ Added Amazon competitor (ID: {amazon_id})")
    except Exception as e:
        print(f"⚠️  Amazon already exists or error: {e}")
    
    # Example 2: Add eBay as a competitor
    ebay_selectors = {
        "price": ".notranslate, .u-flL",
        "title": ".x-item-title-label, h1",
        "availability": ".u-flL, .vi-evo-dd-t",
        "rating": ".ebay-review-star-rating",
        "image": "#icImg, .ux-image-magnify img"
    }
    
    try:
        ebay_id = price_monitor.add_competitor(
            "eBay", 
            "https://www.ebay.com", 
            ebay_selectors
        )
        print(f"✅ Added eBay competitor (ID: {ebay_id})")
    except Exception as e:
        print(f"⚠️  eBay already exists or error: {e}")
    
    # Example 3: Add sample products to monitor
    sample_products = [
        {
            "competitor": "Amazon",
            "name": "Apple iPhone 15 Pro",
            "url": "https://www.amazon.com/dp/B0CHX1W5Y4",
            "sku": "IPHONE15PRO",
            "category": "Electronics"
        },
        {
            "competitor": "Amazon", 
            "name": "Sony WH-1000XM5 Headphones",
            "url": "https://www.amazon.com/dp/B09XS7JWHH",
            "sku": "SONY-WH1000XM5",
            "category": "Electronics"
        }
    ]
    
    product_ids = []
    for product in sample_products:
        try:
            product_id = price_monitor.add_product(
                product["competitor"],
                product["name"],
                product["url"],
                product["sku"],
                product["category"]
            )
            product_ids.append(product_id)
            print(f"✅ Added product: {product['name']} (ID: {product_id})")
        except Exception as e:
            print(f"⚠️  Product already exists or error: {e}")
    
    return product_ids

def setup_price_alerts(product_ids):
    """Set up price alerts for the products"""
    
    print("\n📢 Setting up price alerts...")
    
    for product_id in product_ids:
        try:
            # Alert for 10% price drop
            alert_id = price_monitor.add_price_alert(
                product_id, 
                "price_drop", 
                threshold_percentage=10.0
            )
            print(f"✅ Added price drop alert for product {product_id} (Alert ID: {alert_id})")
        except Exception as e:
            print(f"⚠️  Error adding alert for product {product_id}: {e}")

def run_monitoring_example():
    """Run an example monitoring cycle"""
    
    print("\n🔍 Running monitoring example...")
    
    try:
        # Run monitoring for all products
        results = price_monitor.monitor_all_products(use_selenium=False)
        
        print("\n📊 Monitoring Results:")
        print(f"Total products: {results['total_products']}")
        print(f"Successful scrapes: {results['successful_scrapes']}")
        print(f"Failed scrapes: {results['failed_scrapes']}")
        print(f"Price changes: {results['price_changes']}")
        print(f"Alerts triggered: {results['alerts_triggered']}")
        
        # Show monitoring statistics
        stats = price_monitor.get_monitoring_stats()
        print(f"\n📈 System Statistics:")
        print(f"Total competitors: {stats['total_competitors']}")
        print(f"Total products: {stats['total_products']}")
        print(f"Success rate: {stats['success_rate']:.1f}%")
        
    except Exception as e:
        print(f"❌ Error during monitoring: {e}")

def generate_reports_example():
    """Generate example reports and visualizations"""
    
    print("\n📊 Generating example reports...")
    
    try:
        # Generate monitoring dashboard
        dashboard_path = viz_engine.create_monitoring_dashboard()
        if dashboard_path:
            print(f"✅ Dashboard generated: {dashboard_path}")
        
        # Generate summary report
        summary = viz_engine.generate_summary_report(days=7)
        print(f"\n📋 Summary Report:")
        print(f"Competitors: {summary['total_competitors']}")
        print(f"Products: {summary['total_products']}")
        print(f"Price entries: {summary['total_price_entries']}")
        
        # Show price changes if any
        if summary['price_changes']['total_products_with_changes'] > 0:
            print(f"Products with price changes: {summary['price_changes']['total_products_with_changes']}")
        
    except Exception as e:
        print(f"❌ Error generating reports: {e}")

def test_notifications():
    """Test the notification system"""
    
    print("\n📧 Testing notification system...")
    
    try:
        notification_manager = NotificationManager()
        
        # Test email connection
        if notification_manager.test_email_connection():
            print("✅ Email configuration is working")
            
            # Send test notification
            if notification_manager.send_test_notification():
                print("✅ Test notification sent successfully")
            else:
                print("❌ Failed to send test notification")
        else:
            print("⚠️  Email not configured or connection failed")
            
    except Exception as e:
        print(f"❌ Error testing notifications: {e}")

def main():
    """Main example function"""
    
    print("🛒 E-commerce Competitor Monitoring Agent - Example Usage")
    print("=" * 60)
    
    # Step 1: Set up monitoring
    product_ids = setup_example_monitoring()
    
    # Step 2: Set up alerts
    if product_ids:
        setup_price_alerts(product_ids)
    
    # Step 3: Run monitoring
    run_monitoring_example()
    
    # Step 4: Generate reports
    generate_reports_example()
    
    # Step 5: Test notifications
    test_notifications()
    
    print("\n🎉 Example completed! Check the 'reports' directory for generated visualizations.")
    print("\n💡 Next steps:")
    print("1. Customize CSS selectors for better data extraction")
    print("2. Set up email notifications in .env file")
    print("3. Schedule automatic monitoring with: python cli.py monitor schedule-monitoring")
    print("4. Add more competitors and products using the CLI")

if __name__ == "__main__":
    main()