#!/usr/bin/env python3
"""
E-commerce Competitor Monitoring Agent
Main application entry point
"""

import logging
import signal
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Dict, Any

from core.monitor import CompetitorMonitor
from core.database.manager import DatabaseManager
from config.settings import settings

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

# Global monitor instance
monitor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global monitor
    
    # Startup
    logger.info("Starting E-commerce Competitor Monitoring Agent...")
    
    try:
        # Initialize database
        db = DatabaseManager()
        db.create_tables()
        logger.info("Database initialized successfully")
        
        # Initialize monitor
        monitor = CompetitorMonitor()
        
        # Start monitoring in background
        monitor.start_monitoring()
        logger.info("Monitoring agent started")
        
        yield
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down...")
        if monitor:
            monitor.stop_monitoring()
        logger.info("Shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="E-commerce Competitor Monitoring Agent",
    description="A comprehensive solution for monitoring competitor prices, stock, and promotions",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
@app.get("/")
async def root():
    """Root endpoint with basic information."""
    return {
        "message": "E-commerce Competitor Monitoring Agent",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/api/status")
async def get_status():
    """Get monitoring status."""
    if not monitor:
        raise HTTPException(status_code=503, detail="Monitor not initialized")
    
    return monitor.get_monitoring_status()

@app.post("/api/products")
async def add_product(product_data: Dict[str, Any]):
    """Add a new product to monitor."""
    if not monitor:
        raise HTTPException(status_code=503, detail="Monitor not initialized")
    
    result = monitor.add_product_to_monitor(product_data)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error', 'Unknown error'))
    
    return result

@app.get("/api/products")
async def get_products():
    """Get all monitored products."""
    if not monitor:
        raise HTTPException(status_code=503, detail="Monitor not initialized")
    
    db = DatabaseManager()
    products = db.get_products(active_only=True)
    
    return {
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "url": p.url,
                "competitor": p.competitor,
                "category": p.category,
                "target_price": p.target_price,
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat()
            }
            for p in products
        ]
    }

@app.get("/api/products/{product_id}")
async def get_product(product_id: int):
    """Get a specific product."""
    if not monitor:
        raise HTTPException(status_code=503, detail="Monitor not initialized")
    
    db = DatabaseManager()
    product = db.get_product(product_id)
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {
        "id": product.id,
        "name": product.name,
        "url": product.url,
        "competitor": product.competitor,
        "category": product.category,
        "target_price": product.target_price,
        "created_at": product.created_at.isoformat(),
        "updated_at": product.updated_at.isoformat()
    }

@app.get("/api/products/{product_id}/history")
async def get_product_history(product_id: int, days: int = 30):
    """Get price history for a product."""
    if not monitor:
        raise HTTPException(status_code=503, detail="Monitor not initialized")
    
    return monitor.get_product_statistics(product_id, days)

@app.delete("/api/products/{product_id}")
async def delete_product(product_id: int):
    """Delete a product from monitoring."""
    if not monitor:
        raise HTTPException(status_code=503, detail="Monitor not initialized")
    
    db = DatabaseManager()
    success = db.delete_product(product_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {"message": "Product deleted successfully"}

@app.get("/api/competitors")
async def get_competitors():
    """Get competitor summary."""
    if not monitor:
        raise HTTPException(status_code=503, detail="Monitor not initialized")
    
    return monitor.get_competitor_summary()

@app.post("/api/monitor/start")
async def start_monitoring():
    """Start the monitoring process."""
    if not monitor:
        raise HTTPException(status_code=503, detail="Monitor not initialized")
    
    if monitor.is_running:
        return {"message": "Monitoring is already running"}
    
    monitor.start_monitoring()
    return {"message": "Monitoring started successfully"}

@app.post("/api/monitor/stop")
async def stop_monitoring():
    """Stop the monitoring process."""
    if not monitor:
        raise HTTPException(status_code=503, detail="Monitor not initialized")
    
    if not monitor.is_running:
        return {"message": "Monitoring is not running"}
    
    monitor.stop_monitoring()
    return {"message": "Monitoring stopped successfully"}

@app.post("/api/monitor/run-cycle")
async def run_monitoring_cycle(background_tasks: BackgroundTasks):
    """Run a single monitoring cycle."""
    if not monitor:
        raise HTTPException(status_code=503, detail="Monitor not initialized")
    
    # Run monitoring cycle in background
    background_tasks.add_task(monitor.run_monitoring_cycle)
    
    return {"message": "Monitoring cycle started"}

# Signal handlers for graceful shutdown
def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    if monitor:
        monitor.stop_monitoring()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    # Run the FastAPI server
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_DEBUG,
        log_level="info"
    )