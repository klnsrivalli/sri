from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta
import logging

from models import get_db, Competitor, Product, PriceHistory, AvailabilityHistory, Alert, MonitoringSession
from monitor import CompetitorMonitor
from scraper import CompetitorScraper
from config import settings, COMPETITOR_CONFIGS

# Pydantic models for API
class CompetitorCreate(BaseModel):
    name: str
    base_url: str
    is_active: bool = True

class CompetitorResponse(BaseModel):
    id: int
    name: str
    base_url: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

class ProductCreate(BaseModel):
    competitor_id: int
    name: str
    sku: Optional[str] = None
    url: str
    category: Optional[str] = None
    brand: Optional[str] = None
    is_active: bool = True

class ProductResponse(BaseModel):
    id: int
    competitor_id: int
    name: str
    sku: Optional[str]
    url: str
    category: Optional[str]
    brand: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class AlertResponse(BaseModel):
    id: int
    product_id: int
    alert_type: str
    message: str
    severity: str
    is_read: bool
    created_at: datetime

class MonitoringSessionResponse(BaseModel):
    id: int
    session_name: str
    start_time: datetime
    end_time: Optional[datetime]
    status: str
    products_monitored: int
    successful_scrapes: int
    failed_scrapes: int

class SearchRequest(BaseModel):
    competitor: str
    query: str
    max_results: int = 10

class SearchResponse(BaseModel):
    competitor: str
    query: str
    results: List[Dict[str, Any]]

# Initialize FastAPI app
app = FastAPI(
    title="E-commerce Competitor Monitor API",
    description="API for monitoring competitor prices and availability",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize monitor
monitor = CompetitorMonitor()

# API Routes
@app.get("/")
async def root():
    return {"message": "E-commerce Competitor Monitor API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Competitor endpoints
@app.post("/competitors/", response_model=CompetitorResponse)
async def create_competitor(competitor: CompetitorCreate, db: Session = Depends(get_db)):
    """Create a new competitor"""
    db_competitor = Competitor(**competitor.dict())
    db.add(db_competitor)
    db.commit()
    db.refresh(db_competitor)
    return db_competitor

@app.get("/competitors/", response_model=List[CompetitorResponse])
async def get_competitors(db: Session = Depends(get_db)):
    """Get all competitors"""
    return db.query(Competitor).all()

@app.get("/competitors/{competitor_id}", response_model=CompetitorResponse)
async def get_competitor(competitor_id: int, db: Session = Depends(get_db)):
    """Get a specific competitor"""
    competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return competitor

@app.put("/competitors/{competitor_id}", response_model=CompetitorResponse)
async def update_competitor(competitor_id: int, competitor: CompetitorCreate, db: Session = Depends(get_db)):
    """Update a competitor"""
    db_competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    if not db_competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    for key, value in competitor.dict().items():
        setattr(db_competitor, key, value)
    
    db_competitor.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_competitor)
    return db_competitor

@app.delete("/competitors/{competitor_id}")
async def delete_competitor(competitor_id: int, db: Session = Depends(get_db)):
    """Delete a competitor"""
    competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    db.delete(competitor)
    db.commit()
    return {"message": "Competitor deleted successfully"}

# Product endpoints
@app.post("/products/", response_model=ProductResponse)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product to monitor"""
    # Verify competitor exists
    competitor = db.query(Competitor).filter(Competitor.id == product.competitor_id).first()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/products/", response_model=List[ProductResponse])
async def get_products(
    competitor_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get all products with optional filtering"""
    query = db.query(Product)
    
    if competitor_id:
        query = query.filter(Product.competitor_id == competitor_id)
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    
    return query.all()

@app.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a specific product"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(product_id: int, product: ProductCreate, db: Session = Depends(get_db)):
    """Update a product"""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    for key, value in product.dict().items():
        setattr(db_product, key, value)
    
    db_product.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_product)
    return db_product

@app.delete("/products/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete a product"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}

# Price history endpoints
@app.get("/products/{product_id}/price-history")
async def get_price_history(
    product_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get price history for a product"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    start_date = datetime.utcnow() - timedelta(days=days)
    price_history = db.query(PriceHistory).filter(
        PriceHistory.product_id == product_id,
        PriceHistory.timestamp >= start_date
    ).order_by(PriceHistory.timestamp.desc()).all()
    
    return [
        {
            "id": ph.id,
            "price": ph.price,
            "currency": ph.currency,
            "timestamp": ph.timestamp,
            "source": ph.source
        }
        for ph in price_history
    ]

# Availability history endpoints
@app.get("/products/{product_id}/availability-history")
async def get_availability_history(
    product_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get availability history for a product"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    start_date = datetime.utcnow() - timedelta(days=days)
    availability_history = db.query(AvailabilityHistory).filter(
        AvailabilityHistory.product_id == product_id,
        AvailabilityHistory.timestamp >= start_date
    ).order_by(AvailabilityHistory.timestamp.desc()).all()
    
    return [
        {
            "id": ah.id,
            "is_available": ah.is_available,
            "availability_status": ah.availability_status,
            "timestamp": ah.timestamp,
            "source": ah.source
        }
        for ah in availability_history
    ]

# Alert endpoints
@app.get("/alerts/", response_model=List[AlertResponse])
async def get_alerts(
    is_read: Optional[bool] = None,
    alert_type: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get alerts with optional filtering"""
    query = db.query(Alert)
    
    if is_read is not None:
        query = query.filter(Alert.is_read == is_read)
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    if severity:
        query = query.filter(Alert.severity == severity)
    
    return query.order_by(Alert.created_at.desc()).limit(limit).all()

@app.put("/alerts/{alert_id}/read")
async def mark_alert_read(alert_id: int, db: Session = Depends(get_db)):
    """Mark an alert as read"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_read = True
    db.commit()
    return {"message": "Alert marked as read"}

@app.get("/alerts/unread-count")
async def get_unread_alerts_count(db: Session = Depends(get_db)):
    """Get count of unread alerts"""
    count = db.query(Alert).filter(Alert.is_read == False).count()
    return {"unread_count": count}

# Monitoring session endpoints
@app.get("/monitoring-sessions/", response_model=List[MonitoringSessionResponse])
async def get_monitoring_sessions(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get recent monitoring sessions"""
    return db.query(MonitoringSession).order_by(MonitoringSession.start_time.desc()).limit(limit).all()

@app.get("/monitoring-sessions/{session_id}", response_model=MonitoringSessionResponse)
async def get_monitoring_session(session_id: int, db: Session = Depends(get_db)):
    """Get a specific monitoring session"""
    session = db.query(MonitoringSession).filter(MonitoringSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Monitoring session not found")
    return session

# Search endpoints
@app.post("/search/", response_model=SearchResponse)
async def search_products(search_request: SearchRequest):
    """Search for products on competitor sites"""
    try:
        scraper = CompetitorScraper(search_request.competitor)
        results = scraper.search_products(search_request.query, search_request.max_results)
        
        return SearchResponse(
            competitor=search_request.competitor,
            query=search_request.query,
            results=results
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# Monitoring control endpoints
@app.post("/monitor/start")
async def start_monitoring(background_tasks: BackgroundTasks):
    """Start scheduled monitoring"""
    try:
        background_tasks.add_task(monitor.start_scheduled_monitoring)
        return {"message": "Monitoring started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}")

@app.post("/monitor/stop")
async def stop_monitoring():
    """Stop scheduled monitoring"""
    try:
        monitor.stop_monitoring()
        return {"message": "Monitoring stopped successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop monitoring: {str(e)}")

@app.post("/monitor/run-cycle")
async def run_monitoring_cycle():
    """Run a single monitoring cycle"""
    try:
        results = monitor.run_single_cycle()
        return {"message": "Monitoring cycle completed", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Monitoring cycle failed: {str(e)}")

# Statistics endpoints
@app.get("/stats/overview")
async def get_overview_stats(db: Session = Depends(get_db)):
    """Get overview statistics"""
    total_competitors = db.query(Competitor).filter(Competitor.is_active == True).count()
    total_products = db.query(Product).filter(Product.is_active == True).count()
    total_alerts = db.query(Alert).count()
    unread_alerts = db.query(Alert).filter(Alert.is_read == False).count()
    
    # Get recent monitoring session
    latest_session = db.query(MonitoringSession).order_by(MonitoringSession.start_time.desc()).first()
    
    return {
        "total_competitors": total_competitors,
        "total_products": total_products,
        "total_alerts": total_alerts,
        "unread_alerts": unread_alerts,
        "latest_monitoring_session": {
            "id": latest_session.id if latest_session else None,
            "status": latest_session.status if latest_session else None,
            "start_time": latest_session.start_time if latest_session else None
        }
    }

@app.get("/stats/competitor/{competitor_id}")
async def get_competitor_stats(competitor_id: int, db: Session = Depends(get_db)):
    """Get statistics for a specific competitor"""
    competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    products = db.query(Product).filter(Product.competitor_id == competitor_id).all()
    product_ids = [p.id for p in products]
    
    # Get price changes in last 7 days
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_price_changes = db.query(PriceHistory).filter(
        PriceHistory.product_id.in_(product_ids),
        PriceHistory.timestamp >= week_ago
    ).count()
    
    # Get availability changes in last 7 days
    recent_availability_changes = db.query(AvailabilityHistory).filter(
        AvailabilityHistory.product_id.in_(product_ids),
        AvailabilityHistory.timestamp >= week_ago
    ).count()
    
    return {
        "competitor": competitor.name,
        "total_products": len(products),
        "active_products": len([p for p in products if p.is_active]),
        "recent_price_changes": recent_price_changes,
        "recent_availability_changes": recent_availability_changes
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)