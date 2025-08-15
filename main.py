#!/usr/bin/env python3
"""
E-commerce Competitor Monitoring Agent
Main entry point for running the monitoring system
"""

import argparse
import sys
import logging
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from models import init_db
from monitor import CompetitorMonitor
from api import app as api_app
from dashboard import app as dashboard_app
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('competitor_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def run_monitor():
    """Run the monitoring agent"""
    logger.info("Starting E-commerce Competitor Monitor...")
    
    try:
        # Initialize database
        init_db()
        logger.info("Database initialized successfully")
        
        # Create monitor instance
        monitor = CompetitorMonitor()
        
        # Start monitoring
        logger.info("Starting scheduled monitoring...")
        monitor.start_scheduled_monitoring()
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, stopping monitor...")
        monitor.stop_monitoring()
    except Exception as e:
        logger.error(f"Error in monitor: {e}")
        sys.exit(1)

def run_api():
    """Run the FastAPI server"""
    import uvicorn
    
    logger.info("Starting API server...")
    
    try:
        # Initialize database
        init_db()
        logger.info("Database initialized successfully")
        
        # Run API server
        uvicorn.run(
            api_app,
            host=settings.API_HOST,
            port=settings.API_PORT,
            log_level="info"
        )
        
    except Exception as e:
        logger.error(f"Error starting API server: {e}")
        sys.exit(1)

def run_dashboard():
    """Run the dashboard"""
    logger.info("Starting dashboard...")
    
    try:
        # Run dashboard
        dashboard_app.run_server(
            debug=False,
            host='0.0.0.0',
            port=8050,
            dev_tools_hot_reload=False
        )
        
    except Exception as e:
        logger.error(f"Error starting dashboard: {e}")
        sys.exit(1)

def run_single_cycle():
    """Run a single monitoring cycle"""
    logger.info("Running single monitoring cycle...")
    
    try:
        # Initialize database
        init_db()
        logger.info("Database initialized successfully")
        
        # Create monitor instance and run cycle
        monitor = CompetitorMonitor()
        results = monitor.run_single_cycle()
        
        if results:
            logger.info("Monitoring cycle completed successfully")
            logger.info(f"Results: {results}")
        else:
            logger.error("Monitoring cycle failed")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Error in single cycle: {e}")
        sys.exit(1)

def setup_sample_data():
    """Setup sample competitors and products for testing"""
    from models import get_db, Competitor, Product
    
    logger.info("Setting up sample data...")
    
    try:
        db = next(get_db())
        
        # Add sample competitors
        competitors_data = [
            {"name": "Amazon", "base_url": "https://www.amazon.com"},
            {"name": "Walmart", "base_url": "https://www.walmart.com"},
            {"name": "Target", "base_url": "https://www.target.com"}
        ]
        
        for comp_data in competitors_data:
            existing = db.query(Competitor).filter(Competitor.name == comp_data["name"]).first()
            if not existing:
                competitor = Competitor(**comp_data)
                db.add(competitor)
                logger.info(f"Added competitor: {comp_data['name']}")
        
        db.commit()
        
        # Get competitor IDs
        amazon = db.query(Competitor).filter(Competitor.name == "Amazon").first()
        walmart = db.query(Competitor).filter(Competitor.name == "Walmart").first()
        
        if amazon and walmart:
            # Add sample products
            sample_products = [
                {
                    "competitor_id": amazon.id,
                    "name": "Sample Amazon Product",
                    "url": "https://www.amazon.com/sample-product",
                    "category": "Electronics",
                    "brand": "Sample Brand"
                },
                {
                    "competitor_id": walmart.id,
                    "name": "Sample Walmart Product",
                    "url": "https://www.walmart.com/sample-product",
                    "category": "Electronics",
                    "brand": "Sample Brand"
                }
            ]
            
            for prod_data in sample_products:
                existing = db.query(Product).filter(
                    Product.name == prod_data["name"],
                    Product.competitor_id == prod_data["competitor_id"]
                ).first()
                
                if not existing:
                    product = Product(**prod_data)
                    db.add(product)
                    logger.info(f"Added product: {prod_data['name']}")
        
        db.commit()
        logger.info("Sample data setup completed")
        
    except Exception as e:
        logger.error(f"Error setting up sample data: {e}")
    finally:
        db.close()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="E-commerce Competitor Monitoring Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py monitor          # Run continuous monitoring
  python main.py api              # Run API server
  python main.py dashboard        # Run web dashboard
  python main.py cycle            # Run single monitoring cycle
  python main.py setup            # Setup sample data
        """
    )
    
    parser.add_argument(
        'command',
        choices=['monitor', 'api', 'dashboard', 'cycle', 'setup'],
        help='Command to run'
    )
    
    parser.add_argument(
        '--config',
        help='Path to configuration file'
    )
    
    args = parser.parse_args()
    
    # Execute command
    if args.command == 'monitor':
        run_monitor()
    elif args.command == 'api':
        run_api()
    elif args.command == 'dashboard':
        run_dashboard()
    elif args.command == 'cycle':
        run_single_cycle()
    elif args.command == 'setup':
        setup_sample_data()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()