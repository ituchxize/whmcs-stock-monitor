from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlmodel import Session

from .models import Website, MonitorConfig, StockRecord, MonitorHistory
from .repositories import (
    WebsiteRepository,
    MonitorConfigRepository,
    StockRecordRepository,
    MonitorHistoryRepository
)


class WebsiteService:
    """Service for website management."""
    
    def __init__(self, session: Session):
        self.session = session
        self.repository = WebsiteRepository(session)
    
    def create_website(
        self,
        name: str,
        website_url: str,
        api_identifier: str,
        api_secret: str,
        region: Optional[str] = None,
        is_active: bool = True
    ) -> Website:
        """Create a new website with validation."""
        existing = self.repository.get_by_name(name)
        if existing:
            raise ValueError(f"Website with name '{name}' already exists")
        
        website = Website(
            name=name,
            website_url=website_url,
            api_identifier=api_identifier,
            api_secret=api_secret,
            region=region,
            is_active=is_active
        )
        return self.repository.create(website)
    
    def get_website(self, website_id: int) -> Optional[Website]:
        """Get a website by ID."""
        return self.repository.get_by_id(website_id)
    
    def get_all_websites(self, active_only: bool = False) -> List[Website]:
        """Get all websites."""
        return self.repository.get_all(active_only=active_only)
    
    def update_website(
        self,
        website_id: int,
        name: Optional[str] = None,
        website_url: Optional[str] = None,
        api_identifier: Optional[str] = None,
        api_secret: Optional[str] = None,
        region: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[Website]:
        """Update a website."""
        website = self.repository.get_by_id(website_id)
        if not website:
            return None
        
        if name is not None:
            website.name = name
        if website_url is not None:
            website.website_url = website_url
        if api_identifier is not None:
            website.api_identifier = api_identifier
        if api_secret is not None:
            website.api_secret = api_secret
        if region is not None:
            website.region = region
        if is_active is not None:
            website.is_active = is_active
        
        return self.repository.update(website)
    
    def delete_website(self, website_id: int) -> bool:
        """Delete a website."""
        return self.repository.delete(website_id)


class MonitorConfigService:
    """Service for monitor configuration management."""
    
    def __init__(self, session: Session):
        self.session = session
        self.repository = MonitorConfigRepository(session)
        self.website_repository = WebsiteRepository(session)
    
    def create_monitor(
        self,
        website_id: int,
        product_id: int,
        product_name: Optional[str] = None,
        threshold_low: Optional[int] = None,
        threshold_high: Optional[int] = None,
        notify_on_restock: bool = True,
        notify_on_purchase: bool = True,
        notify_on_threshold: bool = True,
        purchase_link: Optional[str] = None,
        is_active: bool = True,
        status: str = "active"
    ) -> MonitorConfig:
        """Create a new monitor configuration with validation."""
        website = self.website_repository.get_by_id(website_id)
        if not website:
            raise ValueError(f"Website with ID {website_id} does not exist")
        
        existing = self.repository.get_by_website_and_product(website_id, product_id)
        if existing:
            raise ValueError(f"Monitor for product {product_id} on website {website_id} already exists")
        
        monitor = MonitorConfig(
            website_id=website_id,
            product_id=product_id,
            product_name=product_name,
            threshold_low=threshold_low,
            threshold_high=threshold_high,
            notify_on_restock=notify_on_restock,
            notify_on_purchase=notify_on_purchase,
            notify_on_threshold=notify_on_threshold,
            purchase_link=purchase_link,
            is_active=is_active,
            status=status
        )
        return self.repository.create(monitor)
    
    def get_monitor(self, monitor_config_id: int) -> Optional[MonitorConfig]:
        """Get a monitor configuration by ID."""
        return self.repository.get_by_id(monitor_config_id)
    
    def get_active_monitors(self, website_id: Optional[int] = None) -> List[MonitorConfig]:
        """Get active monitor configurations."""
        if website_id:
            return self.repository.get_active_by_website(website_id)
        return self.repository.get_all_active()
    
    def update_monitor(
        self,
        monitor_config_id: int,
        **kwargs
    ) -> Optional[MonitorConfig]:
        """Update a monitor configuration."""
        monitor = self.repository.get_by_id(monitor_config_id)
        if not monitor:
            return None
        
        for key, value in kwargs.items():
            if hasattr(monitor, key) and value is not None:
                setattr(monitor, key, value)
        
        return self.repository.update(monitor)
    
    def delete_monitor(self, monitor_config_id: int) -> bool:
        """Delete a monitor configuration."""
        return self.repository.delete(monitor_config_id)


class MonitoringService:
    """Service for monitoring operations combining multiple repositories."""
    
    def __init__(self, session: Session):
        self.session = session
        self.stock_repo = StockRecordRepository(session)
        self.history_repo = MonitorHistoryRepository(session)
        self.monitor_repo = MonitorConfigRepository(session)
    
    def record_stock_change(
        self,
        monitor_config_id: int,
        quantity: int,
        delta: int,
        stock_control_enabled: bool = False,
        available: bool = True,
        change_type: Optional[str] = None,
        threshold_breached: bool = False,
        threshold_type: Optional[str] = None,
        metadata_json: Optional[str] = None
    ) -> StockRecord:
        """Record a stock change."""
        record = StockRecord(
            monitor_config_id=monitor_config_id,
            quantity=quantity,
            delta=delta,
            stock_control_enabled=stock_control_enabled,
            available=available,
            change_type=change_type,
            threshold_breached=threshold_breached,
            threshold_type=threshold_type,
            metadata_json=metadata_json
        )
        return self.stock_repo.create(record)
    
    def record_history(
        self,
        monitor_config_id: int,
        event_type: str,
        to_quantity: int,
        from_quantity: Optional[int] = None,
        delta: int = 0,
        change_type: Optional[str] = None,
        threshold_breached: bool = False,
        threshold_type: Optional[str] = None,
        threshold_value: Optional[int] = None,
        message: Optional[str] = None,
        metadata_json: Optional[str] = None
    ) -> MonitorHistory:
        """Record a monitor history event."""
        history = MonitorHistory(
            monitor_config_id=monitor_config_id,
            event_type=event_type,
            from_quantity=from_quantity,
            to_quantity=to_quantity,
            delta=delta,
            change_type=change_type,
            threshold_breached=threshold_breached,
            threshold_type=threshold_type,
            threshold_value=threshold_value,
            message=message,
            metadata_json=metadata_json
        )
        return self.history_repo.create(history)
    
    def get_latest_stock(self, monitor_config_id: int) -> Optional[StockRecord]:
        """Get the latest stock record for a monitor."""
        return self.stock_repo.get_latest_by_monitor(monitor_config_id)
    
    def get_stock_history(self, monitor_config_id: int, limit: int = 100) -> List[StockRecord]:
        """Get stock history for a monitor."""
        return self.stock_repo.get_by_monitor(monitor_config_id, limit=limit)
    
    def get_monitor_history(self, monitor_config_id: int, limit: int = 100) -> List[MonitorHistory]:
        """Get monitor history for a monitor."""
        return self.history_repo.get_by_monitor(monitor_config_id, limit=limit)
    
    def get_status_summary(self, monitor_config_id: int) -> Dict[str, Any]:
        """Get a summary of monitor status."""
        monitor = self.monitor_repo.get_by_id(monitor_config_id)
        if not monitor:
            return {}
        
        latest_stock = self.get_latest_stock(monitor_config_id)
        recent_history = self.get_monitor_history(monitor_config_id, limit=10)
        
        return {
            "monitor_id": monitor.id,
            "website_id": monitor.website_id,
            "product_id": monitor.product_id,
            "product_name": monitor.product_name,
            "is_active": monitor.is_active,
            "status": monitor.status,
            "last_checked_at": monitor.last_checked_at.isoformat() if monitor.last_checked_at else None,
            "current_quantity": latest_stock.quantity if latest_stock else None,
            "last_change_type": latest_stock.change_type if latest_stock else None,
            "threshold_breached": latest_stock.threshold_breached if latest_stock else False,
            "recent_events": len(recent_history)
        }
