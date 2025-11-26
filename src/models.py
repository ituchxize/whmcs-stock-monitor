from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship

from .database import Base


class MonitorConfig(Base):
    __tablename__ = "monitor_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, nullable=False, unique=True, index=True)
    product_name = Column(String(255), nullable=True)
    
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    threshold_low = Column(Integer, nullable=True)
    threshold_high = Column(Integer, nullable=True)
    
    notify_on_restock = Column(Boolean, default=True, nullable=False)
    notify_on_purchase = Column(Boolean, default=True, nullable=False)
    notify_on_threshold = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_checked_at = Column(DateTime, nullable=True)
    
    stock_records = relationship("StockRecord", back_populates="monitor_config", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<MonitorConfig(id={self.id}, product_id={self.product_id}, is_active={self.is_active})>"


class StockRecord(Base):
    __tablename__ = "stock_records"
    
    id = Column(Integer, primary_key=True, index=True)
    monitor_config_id = Column(Integer, ForeignKey("monitor_configs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    quantity = Column(Integer, nullable=False)
    delta = Column(Integer, nullable=False, default=0)
    
    stock_control_enabled = Column(Boolean, nullable=False, default=False)
    available = Column(Boolean, nullable=False, default=True)
    
    change_type = Column(String(50), nullable=True)
    threshold_breached = Column(Boolean, default=False, nullable=False)
    threshold_type = Column(String(20), nullable=True)
    
    metadata_json = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    monitor_config = relationship("MonitorConfig", back_populates="stock_records")
    
    __table_args__ = (
        Index('idx_stock_records_monitor_created', 'monitor_config_id', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<StockRecord(id={self.id}, monitor_config_id={self.monitor_config_id}, quantity={self.quantity}, delta={self.delta})>"
