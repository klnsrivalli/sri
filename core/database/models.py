from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
from typing import Optional
import json

Base = declarative_base()

class Product(Base):
    """Product model for storing competitor products to monitor."""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False, unique=True)
    competitor = Column(String(100), nullable=False)
    category = Column(String(100))
    sku = Column(String(100))
    target_price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="product", cascade="all, delete-orphan")

class PriceHistory(Base):
    """Price history model for tracking price changes over time."""
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_available = Column(Boolean, default=True)
    stock_status = Column(String(50))  # "in_stock", "out_of_stock", "limited"
    promotion_text = Column(Text)  # Store promotion details as JSON
    shipping_cost = Column(Float)
    rating = Column(Float)
    review_count = Column(Integer)
    
    # Relationships
    product = relationship("Product", back_populates="price_history")

class Alert(Base):
    """Alert model for storing alert configurations."""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    alert_type = Column(String(50), nullable=False)  # "price_drop", "price_increase", "stock_change", "promotion"
    threshold = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_triggered = Column(DateTime)
    
    # Relationships
    product = relationship("Product", back_populates="alerts")

class Competitor(Base):
    """Competitor model for storing competitor information."""
    __tablename__ = "competitors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    domain = Column(String(100))
    base_url = Column(String(200))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Scraping configuration
    scraper_config = Column(Text)  # JSON configuration for scraping

class MonitoringSession(Base):
    """Session model for tracking monitoring runs."""
    __tablename__ = "monitoring_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    products_processed = Column(Integer, default=0)
    products_updated = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    status = Column(String(20), default="running")  # "running", "completed", "failed"
    error_log = Column(Text)