from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    STOCK_INCREASED = "stock_increased"
    STOCK_DECREASED = "stock_decreased"
    STOCK_UNCHANGED = "stock_unchanged"
    THRESHOLD_BREACH_LOW = "threshold_breach_low"
    THRESHOLD_BREACH_HIGH = "threshold_breach_high"
    MONITOR_ERROR = "monitor_error"
    MONITOR_STARTED = "monitor_started"
    MONITOR_COMPLETED = "monitor_completed"


@dataclass
class StockEvent:
    event_type: EventType
    monitor_config_id: int
    product_id: int
    product_name: Optional[str] = None
    
    quantity: Optional[int] = None
    previous_quantity: Optional[int] = None
    delta: Optional[int] = None
    
    threshold_value: Optional[int] = None
    threshold_type: Optional[str] = None
    
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def __repr__(self) -> str:
        return f"<StockEvent(type={self.event_type.value}, product_id={self.product_id}, delta={self.delta})>"


class EventBus:
    def __init__(self):
        self._handlers: Dict[EventType, List[Callable[[StockEvent], None]]] = {}
        self._global_handlers: List[Callable[[StockEvent], None]] = []
    
    def subscribe(self, event_type: EventType, handler: Callable[[StockEvent], None]) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug(f"Subscribed handler to {event_type.value}")
    
    def subscribe_all(self, handler: Callable[[StockEvent], None]) -> None:
        self._global_handlers.append(handler)
        logger.debug("Subscribed global handler")
    
    def emit(self, event: StockEvent) -> None:
        logger.info(f"Emitting event: {event.event_type.value} for product {event.product_id}")
        
        specific_handlers = self._handlers.get(event.event_type, [])
        all_handlers = specific_handlers + self._global_handlers
        
        for handler in all_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}", exc_info=True)
    
    def clear_handlers(self) -> None:
        self._handlers.clear()
        self._global_handlers.clear()
        logger.debug("Cleared all event handlers")


event_bus = EventBus()


def log_event_handler(event: StockEvent) -> None:
    logger.info(f"Event logged: {event}")


event_bus.subscribe_all(log_event_handler)
