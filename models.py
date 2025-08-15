from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import Optional
import json

Base = declarative_base()

class Competitor(Base):
    __tablename__ = "competitors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    base_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    products = relationship("Product", back_populates="competitor")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    competitor_id = Column(Integer, ForeignKey("competitors.id"))
    name = Column(String(500))
    sku = Column(String(200), index=True)
    url = Column(String(1000))
    category = Column(String(200))
    brand = Column(String(200))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    competitor = relationship("Competitor", back_populates="products")
    price_history = relationship("PriceHistory", back_populates="product")
    availability_history = relationship("AvailabilityHistory", back_populates="product")

class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    price = Column(Float)
    currency = Column(String(10), default="USD")
    timestamp = Column(DateTime, default=datetime.utcnow)
    source = Column(String(100))  # e.g., "web_scraping", "api"
    
    # Relationship
    product = relationship("Product", back_populates="price_history")

class AvailabilityHistory(Base):
    __tablename__ = "availability_history"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    is_available = Column(Boolean)
    availability_status = Column(String(100))  # e.g., "in_stock", "out_of_stock", "limited"
    timestamp = Column(DateTime, default=datetime.utcnow)
    source = Column(String(100))
    
    # Relationship
    product = relationship("Product", back_populates="availability_history")

class MonitoringSession(Base):
    __tablename__ = "monitoring_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_name = Column(String(200))
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    status = Column(String(50))  # "running", "completed", "failed"
    products_monitored = Column(Integer, default=0)
    successful_scrapes = Column(Integer, default=0)
    failed_scrapes = Column(Integer, default=0)
    error_log = Column(Text)

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    alert_type = Column(String(100))  # "price_change", "availability_change", "new_product"
    message = Column(Text)
    severity = Column(String(20))  # "low", "medium", "high"
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Additional data as JSON
    metadata = Column(Text)  # JSON string for additional data
    
    def get_metadata(self) -> dict:
        """Get metadata as dictionary"""
        if self.metadata:
            return json.loads(self.metadata)
        return {}
    
    def set_metadata(self, data: dict):
        """Set metadata as JSON string"""
        self.metadata = json.dumps(data)

# Database connection
from config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)