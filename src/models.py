from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, Column, String, Integer, Text
from sqlalchemy import Index


class Website(SQLModel, table=True):
    __tablename__ = "websites"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, nullable=False, index=True)
    website_url: str = Field(max_length=500, nullable=False)
    api_identifier: str = Field(max_length=255, nullable=False)
    api_secret: str = Field(max_length=500, nullable=False)
    region: Optional[str] = Field(default=None, max_length=100)
    is_active: bool = Field(default=True, nullable=False, index=True)
    
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    
    monitor_configs: List["MonitorConfig"] = Relationship(back_populates="website", cascade_delete=True)
    
    def __repr__(self) -> str:
        return f"<Website(id={self.id}, name={self.name}, url={self.website_url})>"


class MonitorConfig(SQLModel, table=True):
    __tablename__ = "monitor_configs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    website_id: int = Field(foreign_key="websites.id", nullable=False, index=True)
    product_id: int = Field(nullable=False, index=True)
    product_name: Optional[str] = Field(default=None, max_length=255)
    
    is_active: bool = Field(default=True, nullable=False, index=True)
    status: Optional[str] = Field(default="active", max_length=50)
    
    threshold_low: Optional[int] = Field(default=None)
    threshold_high: Optional[int] = Field(default=None)
    
    notify_on_restock: bool = Field(default=True, nullable=False)
    notify_on_purchase: bool = Field(default=True, nullable=False)
    notify_on_threshold: bool = Field(default=True, nullable=False)
    
    purchase_link: Optional[str] = Field(default=None, max_length=500)
    
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    last_checked_at: Optional[datetime] = Field(default=None)
    
    website: Optional[Website] = Relationship(back_populates="monitor_configs")
    stock_records: List["StockRecord"] = Relationship(back_populates="monitor_config", cascade_delete=True)
    monitor_histories: List["MonitorHistory"] = Relationship(back_populates="monitor_config", cascade_delete=True)
    
    def __repr__(self) -> str:
        return f"<MonitorConfig(id={self.id}, website_id={self.website_id}, product_id={self.product_id}, is_active={self.is_active})>"


class StockRecord(SQLModel, table=True):
    __tablename__ = "stock_records"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    monitor_config_id: int = Field(foreign_key="monitor_configs.id", nullable=False, index=True)
    
    quantity: int = Field(nullable=False)
    delta: int = Field(default=0, nullable=False)
    
    stock_control_enabled: bool = Field(default=False, nullable=False)
    available: bool = Field(default=True, nullable=False)
    
    change_type: Optional[str] = Field(default=None, max_length=50)
    threshold_breached: bool = Field(default=False, nullable=False)
    threshold_type: Optional[str] = Field(default=None, max_length=20)
    
    metadata_json: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)
    
    monitor_config: Optional[MonitorConfig] = Relationship(back_populates="stock_records")
    
    __table_args__ = (
        Index('idx_stock_records_monitor_created', 'monitor_config_id', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<StockRecord(id={self.id}, monitor_config_id={self.monitor_config_id}, quantity={self.quantity}, delta={self.delta})>"


class MonitorHistory(SQLModel, table=True):
    __tablename__ = "monitor_histories"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    monitor_config_id: int = Field(foreign_key="monitor_configs.id", nullable=False, index=True)
    
    event_type: str = Field(max_length=50, nullable=False, index=True)
    from_quantity: Optional[int] = Field(default=None)
    to_quantity: int = Field(nullable=False)
    delta: int = Field(default=0, nullable=False)
    
    change_type: Optional[str] = Field(default=None, max_length=50)
    
    threshold_breached: bool = Field(default=False, nullable=False)
    threshold_type: Optional[str] = Field(default=None, max_length=20)
    threshold_value: Optional[int] = Field(default=None)
    
    message: Optional[str] = Field(default=None, max_length=500)
    metadata_json: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)
    
    monitor_config: Optional[MonitorConfig] = Relationship(back_populates="monitor_histories")
    
    __table_args__ = (
        Index('idx_monitor_histories_config_created', 'monitor_config_id', 'created_at'),
        Index('idx_monitor_histories_event_type', 'event_type', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<MonitorHistory(id={self.id}, monitor_config_id={self.monitor_config_id}, event_type={self.event_type}, delta={self.delta})>"
