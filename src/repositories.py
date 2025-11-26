from typing import Optional, List
from datetime import datetime
from sqlmodel import Session, select
from sqlalchemy import desc

from .models import Website, MonitorConfig, StockRecord, MonitorHistory


class WebsiteRepository:
    """Repository for Website CRUD operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, website: Website) -> Website:
        """Create a new website."""
        website.created_at = datetime.utcnow()
        website.updated_at = datetime.utcnow()
        self.session.add(website)
        self.session.commit()
        self.session.refresh(website)
        return website
    
    def get_by_id(self, website_id: int) -> Optional[Website]:
        """Get a website by ID."""
        return self.session.get(Website, website_id)
    
    def get_by_name(self, name: str) -> Optional[Website]:
        """Get a website by name."""
        statement = select(Website).where(Website.name == name)
        return self.session.exec(statement).first()
    
    def get_all(self, active_only: bool = False) -> List[Website]:
        """Get all websites, optionally filtering by active status."""
        statement = select(Website)
        if active_only:
            statement = statement.where(Website.is_active == True)
        return list(self.session.exec(statement).all())
    
    def update(self, website: Website) -> Website:
        """Update a website."""
        website.updated_at = datetime.utcnow()
        self.session.add(website)
        self.session.commit()
        self.session.refresh(website)
        return website
    
    def delete(self, website_id: int) -> bool:
        """Delete a website."""
        website = self.get_by_id(website_id)
        if website:
            self.session.delete(website)
            self.session.commit()
            return True
        return False


class MonitorConfigRepository:
    """Repository for MonitorConfig CRUD operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, monitor_config: MonitorConfig) -> MonitorConfig:
        """Create a new monitor configuration."""
        monitor_config.created_at = datetime.utcnow()
        monitor_config.updated_at = datetime.utcnow()
        self.session.add(monitor_config)
        self.session.commit()
        self.session.refresh(monitor_config)
        return monitor_config
    
    def get_by_id(self, monitor_config_id: int) -> Optional[MonitorConfig]:
        """Get a monitor configuration by ID."""
        return self.session.get(MonitorConfig, monitor_config_id)
    
    def get_by_website_and_product(self, website_id: int, product_id: int) -> Optional[MonitorConfig]:
        """Get a monitor configuration by website ID and product ID."""
        statement = select(MonitorConfig).where(
            MonitorConfig.website_id == website_id,
            MonitorConfig.product_id == product_id
        )
        return self.session.exec(statement).first()
    
    def get_active_by_website(self, website_id: int) -> List[MonitorConfig]:
        """Get all active monitor configurations for a website."""
        statement = select(MonitorConfig).where(
            MonitorConfig.website_id == website_id,
            MonitorConfig.is_active == True
        )
        return list(self.session.exec(statement).all())
    
    def get_all_active(self) -> List[MonitorConfig]:
        """Get all active monitor configurations across all websites."""
        statement = select(MonitorConfig).where(MonitorConfig.is_active == True)
        return list(self.session.exec(statement).all())
    
    def update(self, monitor_config: MonitorConfig) -> MonitorConfig:
        """Update a monitor configuration."""
        monitor_config.updated_at = datetime.utcnow()
        self.session.add(monitor_config)
        self.session.commit()
        self.session.refresh(monitor_config)
        return monitor_config
    
    def delete(self, monitor_config_id: int) -> bool:
        """Delete a monitor configuration."""
        monitor_config = self.get_by_id(monitor_config_id)
        if monitor_config:
            self.session.delete(monitor_config)
            self.session.commit()
            return True
        return False


class StockRecordRepository:
    """Repository for StockRecord operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, stock_record: StockRecord) -> StockRecord:
        """Create a new stock record."""
        stock_record.created_at = datetime.utcnow()
        self.session.add(stock_record)
        self.session.commit()
        self.session.refresh(stock_record)
        return stock_record
    
    def get_latest_by_monitor(self, monitor_config_id: int) -> Optional[StockRecord]:
        """Get the latest stock record for a monitor configuration."""
        statement = (
            select(StockRecord)
            .where(StockRecord.monitor_config_id == monitor_config_id)
            .order_by(desc(StockRecord.created_at))
        )
        return self.session.exec(statement).first()
    
    def get_by_monitor(self, monitor_config_id: int, limit: int = 100) -> List[StockRecord]:
        """Get stock records for a monitor configuration."""
        statement = (
            select(StockRecord)
            .where(StockRecord.monitor_config_id == monitor_config_id)
            .order_by(desc(StockRecord.created_at))
            .limit(limit)
        )
        return list(self.session.exec(statement).all())


class MonitorHistoryRepository:
    """Repository for MonitorHistory operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, history: MonitorHistory) -> MonitorHistory:
        """Create a new monitor history entry."""
        history.created_at = datetime.utcnow()
        self.session.add(history)
        self.session.commit()
        self.session.refresh(history)
        return history
    
    def get_by_monitor(self, monitor_config_id: int, limit: int = 100) -> List[MonitorHistory]:
        """Get monitor history for a monitor configuration."""
        statement = (
            select(MonitorHistory)
            .where(MonitorHistory.monitor_config_id == monitor_config_id)
            .order_by(desc(MonitorHistory.created_at))
            .limit(limit)
        )
        return list(self.session.exec(statement).all())
    
    def get_by_event_type(self, event_type: str, limit: int = 100) -> List[MonitorHistory]:
        """Get monitor history by event type."""
        statement = (
            select(MonitorHistory)
            .where(MonitorHistory.event_type == event_type)
            .order_by(desc(MonitorHistory.created_at))
            .limit(limit)
        )
        return list(self.session.exec(statement).all())
