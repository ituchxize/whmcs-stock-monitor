import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from .whmcs_client import WhmcsClient
from .models import MonitorConfig, StockRecord
from .events import event_bus, StockEvent, EventType
from .database import get_db_context
from .config import settings
from .exceptions import WhmcsClientError

logger = logging.getLogger(__name__)


class StockChangeDetector:
    RESTOCK_THRESHOLD = 0
    
    def __init__(self):
        pass
    
    def detect_change_type(self, current_quantity: int, previous_quantity: Optional[int], delta: int) -> str:
        if previous_quantity is None:
            return "initial"
        
        if delta > self.RESTOCK_THRESHOLD:
            return "restock"
        elif delta < 0:
            return "purchase"
        else:
            return "unchanged"
    
    def check_threshold_breach(
        self,
        current_quantity: int,
        threshold_low: Optional[int],
        threshold_high: Optional[int]
    ) -> tuple[bool, Optional[str]]:
        if threshold_low is not None and current_quantity <= threshold_low:
            return True, "low"
        
        if threshold_high is not None and current_quantity >= threshold_high:
            return True, "high"
        
        return False, None


class MonitoringEngine:
    def __init__(self, whmcs_client: Optional[WhmcsClient] = None):
        self.whmcs_client = whmcs_client
        self.change_detector = StockChangeDetector()
    
    def _get_whmcs_client(self) -> WhmcsClient:
        if self.whmcs_client:
            return self.whmcs_client
        
        return WhmcsClient(
            api_url=settings.whmcs_api_url,
            api_identifier=settings.whmcs_api_identifier,
            api_secret=settings.whmcs_api_secret,
            timeout=settings.whmcs_timeout,
            cache_ttl=settings.whmcs_cache_ttl
        )
    
    def run_monitoring_cycle(self) -> Dict[str, Any]:
        logger.info("Starting monitoring cycle")
        
        event_bus.emit(StockEvent(
            event_type=EventType.MONITOR_STARTED,
            monitor_config_id=0,
            product_id=0,
            metadata={"timestamp": datetime.utcnow().isoformat()}
        ))
        
        results = {
            "started_at": datetime.utcnow().isoformat(),
            "monitors_checked": 0,
            "records_created": 0,
            "errors": 0,
            "changes_detected": 0,
            "threshold_breaches": 0
        }
        
        with get_db_context() as db:
            active_monitors = self._get_active_monitors(db)
            results["monitors_checked"] = len(active_monitors)
            
            if not active_monitors:
                logger.info("No active monitors found")
                results["completed_at"] = datetime.utcnow().isoformat()
                return results
            
            whmcs_client = self._get_whmcs_client()
            
            for monitor in active_monitors:
                try:
                    record_created, change_detected, threshold_breached = self._check_monitor(
                        db, monitor, whmcs_client
                    )
                    
                    if record_created:
                        results["records_created"] += 1
                    if change_detected:
                        results["changes_detected"] += 1
                    if threshold_breached:
                        results["threshold_breaches"] += 1
                    
                    monitor.last_checked_at = datetime.utcnow()
                    db.commit()
                    
                except Exception as e:
                    logger.error(f"Error checking monitor {monitor.id} (product {monitor.product_id}): {e}", exc_info=True)
                    results["errors"] += 1
                    
                    event_bus.emit(StockEvent(
                        event_type=EventType.MONITOR_ERROR,
                        monitor_config_id=monitor.id,
                        product_id=monitor.product_id,
                        product_name=monitor.product_name,
                        error_message=str(e),
                        metadata={"error_type": type(e).__name__}
                    ))
                    
                    db.rollback()
        
        results["completed_at"] = datetime.utcnow().isoformat()
        logger.info(f"Monitoring cycle completed: {results}")
        
        event_bus.emit(StockEvent(
            event_type=EventType.MONITOR_COMPLETED,
            monitor_config_id=0,
            product_id=0,
            metadata=results
        ))
        
        return results
    
    def _get_active_monitors(self, db: Session) -> List[MonitorConfig]:
        return db.query(MonitorConfig).filter(MonitorConfig.is_active == True).all()
    
    def _get_latest_stock_record(self, db: Session, monitor_config_id: int) -> Optional[StockRecord]:
        return (
            db.query(StockRecord)
            .filter(StockRecord.monitor_config_id == monitor_config_id)
            .order_by(StockRecord.created_at.desc())
            .first()
        )
    
    def _check_monitor(
        self,
        db: Session,
        monitor: MonitorConfig,
        whmcs_client: WhmcsClient
    ) -> tuple[bool, bool, bool]:
        logger.debug(f"Checking monitor {monitor.id} for product {monitor.product_id}")
        
        inventory = whmcs_client.get_product_inventory(monitor.product_id, use_cache=False)
        
        current_quantity = inventory['quantity']
        stock_control = inventory['stock_control']
        available = inventory['available']
        
        if monitor.product_name is None and inventory.get('name'):
            monitor.product_name = inventory['name']
        
        latest_record = self._get_latest_stock_record(db, monitor.id)
        previous_quantity = latest_record.quantity if latest_record else None
        
        delta = current_quantity - previous_quantity if previous_quantity is not None else 0
        
        change_type = self.change_detector.detect_change_type(current_quantity, previous_quantity, delta)
        
        threshold_breached, threshold_type = self.change_detector.check_threshold_breach(
            current_quantity, monitor.threshold_low, monitor.threshold_high
        )
        
        new_record = StockRecord(
            monitor_config_id=monitor.id,
            quantity=current_quantity,
            delta=delta,
            stock_control_enabled=stock_control,
            available=available,
            change_type=change_type,
            threshold_breached=threshold_breached,
            threshold_type=threshold_type,
            created_at=datetime.utcnow()
        )
        
        db.add(new_record)
        db.flush()
        
        self._emit_events(monitor, new_record, previous_quantity)
        
        change_detected = delta != 0
        
        return True, change_detected, threshold_breached
    
    def _emit_events(
        self,
        monitor: MonitorConfig,
        record: StockRecord,
        previous_quantity: Optional[int]
    ) -> None:
        base_event_data = {
            "monitor_config_id": monitor.id,
            "product_id": monitor.product_id,
            "product_name": monitor.product_name,
            "quantity": record.quantity,
            "previous_quantity": previous_quantity,
            "delta": record.delta,
            "metadata": {
                "change_type": record.change_type,
                "stock_control": record.stock_control_enabled,
                "available": record.available
            }
        }
        
        if record.threshold_breached and monitor.notify_on_threshold:
            event_type = (
                EventType.THRESHOLD_BREACH_LOW if record.threshold_type == "low"
                else EventType.THRESHOLD_BREACH_HIGH
            )
            
            threshold_value = (
                monitor.threshold_low if record.threshold_type == "low"
                else monitor.threshold_high
            )
            
            event_bus.emit(StockEvent(
                event_type=event_type,
                threshold_value=threshold_value,
                threshold_type=record.threshold_type,
                **base_event_data
            ))
        
        if record.delta > 0 and monitor.notify_on_restock:
            event_bus.emit(StockEvent(
                event_type=EventType.STOCK_INCREASED,
                **base_event_data
            ))
        elif record.delta < 0 and monitor.notify_on_purchase:
            event_bus.emit(StockEvent(
                event_type=EventType.STOCK_DECREASED,
                **base_event_data
            ))
        elif record.delta == 0 and previous_quantity is not None:
            event_bus.emit(StockEvent(
                event_type=EventType.STOCK_UNCHANGED,
                **base_event_data
            ))
