#!/usr/bin/env python3
import click
import json
import sys
import schedule
import time
import threading
from datetime import datetime
from typing import List, Dict
import logging

from config import config, CompetitorConfig
from monitor import price_monitor
from visualizations import viz_engine
from notifications import NotificationManager
from models import init_db, SessionLocal, Competitor, Product, PriceHistory
from scraper import scraping_manager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """E-commerce Competitor Monitoring Agent
    
    A comprehensive tool for monitoring competitor prices, tracking changes,
    and generating insights for e-commerce businesses.
    """
    # Initialize database on startup
    init_db()

@cli.group()
def competitor():
    """Manage competitors"""
    pass

@competitor.command()
@click.argument('name')
@click.argument('base_url')
@click.option('--selectors', '-s', help='JSON string of CSS selectors')
def add(name, base_url, selectors):
    """Add a new competitor"""
    try:
        if selectors:
            selector_dict = json.loads(selectors)
        else:
            # Default selectors - user should customize these
            selector_dict = {
                'price': '.price, .price-current, [data-price]',
                'title': 'h1, .product-title, .item-title',
                'availability': '.availability, .stock-status',
                'rating': '.rating, .stars, .review-score'
            }
        
        competitor_id = price_monitor.add_competitor(name, base_url, selector_dict)
        click.echo(f"✅ Added competitor '{name}' with ID {competitor_id}")
        click.echo("💡 Remember to customize the CSS selectors for accurate data extraction!")
        
    except Exception as e:
        click.echo(f"❌ Error adding competitor: {str(e)}", err=True)
        sys.exit(1)

@competitor.command()
def list():
    """List all competitors"""
    db = SessionLocal()
    try:
        competitors = db.query(Competitor).all()
        if not competitors:
            click.echo("No competitors found. Use 'competitor add' to add one.")
            return
        
        click.echo("\n📊 Competitors:")
        click.echo("-" * 50)
        for comp in competitors:
            status = "🟢 Active" if comp.is_active else "🔴 Inactive"
            click.echo(f"ID: {comp.id} | {comp.name} | {status}")
            click.echo(f"   URL: {comp.base_url}")
            click.echo(f"   Added: {comp.created_at.strftime('%Y-%m-%d %H:%M')}")
            click.echo()
    finally:
        db.close()

@competitor.command()
@click.argument('competitor_id', type=int)
def deactivate(competitor_id):
    """Deactivate a competitor"""
    db = SessionLocal()
    try:
        competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
        if not competitor:
            click.echo(f"❌ Competitor {competitor_id} not found")
            return
        
        competitor.is_active = False
        db.commit()
        click.echo(f"✅ Deactivated competitor '{competitor.name}'")
    finally:
        db.close()

@cli.group()
def product():
    """Manage products to monitor"""
    pass

@product.command()
@click.argument('competitor_name')
@click.argument('product_name')
@click.argument('url')
@click.option('--sku', help='Product SKU')
@click.option('--category', help='Product category')
def add(competitor_name, product_name, url, sku, category):
    """Add a product to monitor"""
    try:
        product_id = price_monitor.add_product(
            competitor_name, product_name, url, sku, category
        )
        click.echo(f"✅ Added product '{product_name}' with ID {product_id}")
    except Exception as e:
        click.echo(f"❌ Error adding product: {str(e)}", err=True)
        sys.exit(1)

@product.command()
def list():
    """List all products"""
    db = SessionLocal()
    try:
        products = db.query(Product).join(Competitor).all()
        if not products:
            click.echo("No products found. Use 'product add' to add one.")
            return
        
        click.echo("\n📦 Products:")
        click.echo("-" * 70)
        for prod in products:
            status = "🟢 Active" if prod.is_active else "🔴 Inactive"
            click.echo(f"ID: {prod.id} | {prod.name[:40]}...")
            click.echo(f"   Competitor: {prod.competitor.name} | {status}")
            click.echo(f"   URL: {prod.url}")
            if prod.sku:
                click.echo(f"   SKU: {prod.sku}")
            click.echo()
    finally:
        db.close()

@product.command()
@click.argument('product_id', type=int)
@click.option('--selenium', is_flag=True, help='Use Selenium for scraping')
def test(product_id, selenium):
    """Test scraping a specific product"""
    try:
        click.echo(f"🔍 Testing product {product_id}...")
        result = price_monitor.scrape_and_store(product_id, selenium)
        
        if result:
            click.echo(f"✅ Successfully scraped product!")
            click.echo(f"   Price: ${result.price:.2f} {result.currency}")
            click.echo(f"   Availability: {result.availability or 'Unknown'}")
            if result.rating:
                click.echo(f"   Rating: {result.rating}/5")
        else:
            click.echo("❌ Failed to scrape product data")
    except Exception as e:
        click.echo(f"❌ Error testing product: {str(e)}", err=True)

@cli.group()
def monitor():
    """Monitoring operations"""
    pass

@monitor.command()
@click.option('--selenium', is_flag=True, help='Use Selenium for scraping')
@click.option('--notify', is_flag=True, help='Send summary notification')
def run(selenium, notify):
    """Run monitoring for all products"""
    click.echo("🚀 Starting competitor monitoring...")
    
    try:
        results = price_monitor.monitor_all_products(selenium)
        
        click.echo("\n📊 Monitoring Results:")
        click.echo("-" * 30)
        click.echo(f"Total products: {results['total_products']}")
        click.echo(f"Successful scrapes: {results['successful_scrapes']}")
        click.echo(f"Failed scrapes: {results['failed_scrapes']}")
        click.echo(f"Price changes: {results['price_changes']}")
        click.echo(f"Alerts triggered: {results['alerts_triggered']}")
        
        success_rate = (results['successful_scrapes'] / results['total_products'] * 100) if results['total_products'] > 0 else 0
        click.echo(f"Success rate: {success_rate:.1f}%")
        
        if notify:
            notification_manager = NotificationManager()
            notification_manager.send_monitoring_summary(results)
            click.echo("📧 Summary notification sent")
            
    except Exception as e:
        click.echo(f"❌ Error during monitoring: {str(e)}", err=True)
        sys.exit(1)

@monitor.command()
@click.option('--interval', '-i', default=3600, help='Check interval in seconds (default: 3600)')
@click.option('--selenium', is_flag=True, help='Use Selenium for scraping')
def schedule_monitoring(interval, selenium):
    """Schedule automatic monitoring"""
    click.echo(f"⏰ Scheduling monitoring every {interval} seconds...")
    
    def run_monitoring():
        try:
            logger.info("Running scheduled monitoring")
            results = price_monitor.monitor_all_products(selenium)
            logger.info(f"Monitoring completed: {results}")
        except Exception as e:
            logger.error(f"Error in scheduled monitoring: {str(e)}")
    
    # Schedule the job
    schedule.every(interval).seconds.do(run_monitoring)
    
    # Run the scheduler in a separate thread
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    click.echo("✅ Monitoring scheduled. Press Ctrl+C to stop.")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(60)
            click.echo(f"📊 Scheduler running... Next run in {schedule.idle_seconds():.0f}s")
    except KeyboardInterrupt:
        click.echo("\n⏹️  Monitoring stopped")

@monitor.command()
def stats():
    """Show monitoring statistics"""
    try:
        stats = price_monitor.get_monitoring_stats()
        
        click.echo("\n📈 Monitoring Statistics:")
        click.echo("-" * 40)
        click.echo(f"Total competitors: {stats['total_competitors']}")
        click.echo(f"Total products: {stats['total_products']}")
        click.echo(f"Total price entries: {stats['total_price_entries']}")
        click.echo(f"Active alerts: {stats['active_alerts']}")
        click.echo(f"Recent scrapes (24h): {stats['recent_scrapes']}")
        click.echo(f"Recent successes (24h): {stats['recent_successes']}")
        click.echo(f"Success rate: {stats['success_rate']:.1f}%")
        
    except Exception as e:
        click.echo(f"❌ Error retrieving stats: {str(e)}", err=True)

@cli.group()
def alert():
    """Manage price alerts"""
    pass

@alert.command()
@click.argument('product_id', type=int)
@click.argument('alert_type', type=click.Choice(['price_drop', 'price_increase']))
@click.option('--threshold-value', type=float, help='Absolute price threshold')
@click.option('--threshold-percentage', type=float, help='Percentage change threshold')
def add(product_id, alert_type, threshold_value, threshold_percentage):
    """Add a price alert"""
    if not threshold_value and not threshold_percentage:
        click.echo("❌ Must specify either --threshold-value or --threshold-percentage")
        return
    
    try:
        alert_id = price_monitor.add_price_alert(
            product_id, alert_type, threshold_value, threshold_percentage
        )
        click.echo(f"✅ Added {alert_type} alert with ID {alert_id}")
    except Exception as e:
        click.echo(f"❌ Error adding alert: {str(e)}", err=True)

@cli.group()
def report():
    """Generate reports and visualizations"""
    pass

@report.command()
@click.argument('product_id', type=int)
@click.option('--days', '-d', default=30, help='Number of days to include')
def price_history(product_id, days):
    """Generate price history chart for a product"""
    try:
        filepath = viz_engine.create_price_history_chart(product_id, days)
        if filepath:
            click.echo(f"📊 Price history chart generated: {filepath}")
        else:
            click.echo("❌ No data available for chart generation")
    except Exception as e:
        click.echo(f"❌ Error generating chart: {str(e)}", err=True)

@report.command()
@click.argument('product_pattern')
def compare(product_pattern):
    """Generate competitor comparison chart"""
    try:
        filepath = viz_engine.create_competitor_comparison_chart(product_pattern)
        if filepath:
            click.echo(f"📊 Comparison chart generated: {filepath}")
        else:
            click.echo("❌ No matching products found")
    except Exception as e:
        click.echo(f"❌ Error generating comparison: {str(e)}", err=True)

@report.command()
@click.option('--days', '-d', default=30, help='Number of days to analyze')
def trends(days):
    """Generate price trend analysis"""
    try:
        filepath = viz_engine.create_price_trend_analysis(days)
        if filepath:
            click.echo(f"📊 Trend analysis generated: {filepath}")
        else:
            click.echo("❌ No data available for analysis")
    except Exception as e:
        click.echo(f"❌ Error generating trends: {str(e)}", err=True)

@report.command()
def dashboard():
    """Generate monitoring dashboard"""
    try:
        filepath = viz_engine.create_monitoring_dashboard()
        if filepath:
            click.echo(f"📊 Dashboard generated: {filepath}")
        else:
            click.echo("❌ Failed to generate dashboard")
    except Exception as e:
        click.echo(f"❌ Error generating dashboard: {str(e)}", err=True)

@report.command()
@click.option('--days', '-d', default=7, help='Number of days to include in report')
@click.option('--format', '-f', type=click.Choice(['json', 'text']), default='text', help='Output format')
def summary(days, format):
    """Generate summary report"""
    try:
        report_data = viz_engine.generate_summary_report(days)
        
        if format == 'json':
            # Convert datetime to string for JSON serialization
            report_data['generated_at'] = report_data['generated_at'].isoformat()
            click.echo(json.dumps(report_data, indent=2, default=str))
        else:
            click.echo(f"\n📋 Summary Report - Last {days} Days")
            click.echo("=" * 50)
            click.echo(f"Generated: {report_data['generated_at'].strftime('%Y-%m-%d %H:%M:%S')}")
            click.echo(f"Total competitors: {report_data['total_competitors']}")
            click.echo(f"Total products: {report_data['total_products']}")
            click.echo(f"Price entries: {report_data['total_price_entries']}")
            
            price_changes = report_data['price_changes']
            click.echo(f"\nPrice Changes: {price_changes['total_products_with_changes']}")
            
            if price_changes['biggest_increases']:
                click.echo("\n📈 Biggest Price Increases:")
                for item in price_changes['biggest_increases']:
                    click.echo(f"  • {item['product_name']} ({item['competitor']})")
                    click.echo(f"    ${item['first_price']:.2f} → ${item['last_price']:.2f} (+{item['change_percentage']:.1f}%)")
            
            if price_changes['biggest_decreases']:
                click.echo("\n📉 Biggest Price Decreases:")
                for item in price_changes['biggest_decreases']:
                    click.echo(f"  • {item['product_name']} ({item['competitor']})")
                    click.echo(f"    ${item['first_price']:.2f} → ${item['last_price']:.2f} ({item['change_percentage']:.1f}%)")
            
            click.echo("\n🏪 Competitor Stats:")
            for comp in report_data['competitor_stats']:
                click.echo(f"  • {comp['name']}: {comp['product_count']} products, avg ${comp['average_price']:.2f}")
                
    except Exception as e:
        click.echo(f"❌ Error generating summary: {str(e)}", err=True)

@cli.group()
def config_cmd():
    """Configuration management"""
    pass

@config_cmd.command()
def show():
    """Show current configuration"""
    click.echo("\n⚙️  Current Configuration:")
    click.echo("-" * 30)
    click.echo(f"Database URL: {config.database_url}")
    click.echo(f"Check interval: {config.monitoring.check_interval}s")
    click.echo(f"Price change threshold: {config.monitoring.price_change_threshold * 100}%")
    click.echo(f"Max retries: {config.monitoring.max_retries}")
    click.echo(f"Timeout: {config.monitoring.timeout}s")
    
    click.echo(f"\nEmail notifications: {'✅ Enabled' if config.notifications.email_enabled else '❌ Disabled'}")
    if config.notifications.email_enabled:
        click.echo(f"SMTP server: {config.notifications.smtp_server}:{config.notifications.smtp_port}")
        click.echo(f"Recipients: {len(config.notifications.recipients)} configured")

@config_cmd.command()
def test_email():
    """Test email notification configuration"""
    try:
        notification_manager = NotificationManager()
        if notification_manager.test_email_connection():
            click.echo("✅ Email configuration is working")
            
            # Send test notification
            if click.confirm("Send a test notification?"):
                if notification_manager.send_test_notification():
                    click.echo("📧 Test notification sent successfully")
                else:
                    click.echo("❌ Failed to send test notification")
        else:
            click.echo("❌ Email configuration test failed")
    except Exception as e:
        click.echo(f"❌ Error testing email: {str(e)}", err=True)

@cli.command()
def init():
    """Initialize the monitoring system"""
    try:
        # Initialize database
        init_db()
        click.echo("✅ Database initialized")
        
        # Test email configuration if enabled
        if config.notifications.email_enabled:
            notification_manager = NotificationManager()
            if notification_manager.test_email_connection():
                click.echo("✅ Email configuration verified")
            else:
                click.echo("⚠️  Email configuration issue detected")
        
        click.echo("\n🎉 Competitor monitoring system initialized successfully!")
        click.echo("\n📖 Next steps:")
        click.echo("1. Add competitors: competitor add <name> <url>")
        click.echo("2. Add products: product add <competitor> <product_name> <url>")
        click.echo("3. Run monitoring: monitor run")
        click.echo("4. Generate reports: report dashboard")
        
    except Exception as e:
        click.echo(f"❌ Initialization failed: {str(e)}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    cli()