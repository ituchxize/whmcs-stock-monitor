from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.persistence.database import Base


class MonitorConfig(Base):
    __tablename__ = "monitor_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    config_option_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    config_option_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    check_interval: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    
    notify_on_restock: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_on_purchase: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_on_stock_low: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    low_stock_threshold: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    stock_records: Mapped[List["StockRecord"]] = relationship(
        "StockRecord",
        back_populates="monitor_config",
        cascade="all, delete-orphan"
    )
    
    notification_logs: Mapped[List["NotificationLog"]] = relationship(
        "NotificationLog",
        back_populates="monitor_config",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_product_config", "product_id", "config_option_id"),
        Index("idx_active_configs", "is_active", "product_id"),
    )

    def __repr__(self) -> str:
        return f"<MonitorConfig(id={self.id}, product_id={self.product_id}, product_name='{self.product_name}')>"


class StockRecord(Base):
    __tablename__ = "stock_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    monitor_config_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("monitor_configs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    stock_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    stock_control_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    change_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    change_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    change_amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    monitor_config: Mapped["MonitorConfig"] = relationship(
        "MonitorConfig",
        back_populates="stock_records"
    )

    __table_args__ = (
        Index("idx_monitor_recorded", "monitor_config_id", "recorded_at"),
        Index("idx_change_detection", "change_detected", "change_type"),
    )

    def __repr__(self) -> str:
        return f"<StockRecord(id={self.id}, monitor_config_id={self.monitor_config_id}, stock={self.stock_quantity})>"


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    monitor_config_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("monitor_configs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(50), default="telegram", nullable=False)
    
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        index=True
    )
    
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    monitor_config: Mapped["MonitorConfig"] = relationship(
        "MonitorConfig",
        back_populates="notification_logs"
    )

    __table_args__ = (
        Index("idx_notification_status", "status", "created_at"),
        Index("idx_notification_type_status", "notification_type", "status"),
    )

    def __repr__(self) -> str:
        return f"<NotificationLog(id={self.id}, type='{self.notification_type}', status='{self.status}')>"
