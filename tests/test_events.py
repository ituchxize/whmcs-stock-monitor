import pytest
from datetime import datetime

from src.events import EventBus, StockEvent, EventType


class TestStockEvent:
    def test_create_stock_event(self):
        event = StockEvent(
            event_type=EventType.STOCK_INCREASED,
            monitor_config_id=1,
            product_id=123,
            product_name="Test Product",
            quantity=20,
            previous_quantity=10,
            delta=10
        )
        
        assert event.event_type == EventType.STOCK_INCREASED
        assert event.monitor_config_id == 1
        assert event.product_id == 123
        assert event.quantity == 20
        assert event.delta == 10
    
    def test_to_dict(self):
        event = StockEvent(
            event_type=EventType.STOCK_DECREASED,
            monitor_config_id=1,
            product_id=123,
            delta=-5
        )
        
        event_dict = event.to_dict()
        
        assert event_dict["event_type"] == "stock_decreased"
        assert event_dict["product_id"] == 123
        assert event_dict["delta"] == -5
        assert "timestamp" in event_dict
    
    def test_threshold_event(self):
        event = StockEvent(
            event_type=EventType.THRESHOLD_BREACH_LOW,
            monitor_config_id=1,
            product_id=123,
            quantity=3,
            threshold_value=5,
            threshold_type="low"
        )
        
        assert event.threshold_value == 5
        assert event.threshold_type == "low"


class TestEventBus:
    def test_subscribe_and_emit(self):
        bus = EventBus()
        events_received = []
        
        def handler(event):
            events_received.append(event)
        
        bus.subscribe(EventType.STOCK_INCREASED, handler)
        
        event = StockEvent(
            event_type=EventType.STOCK_INCREASED,
            monitor_config_id=1,
            product_id=123,
            delta=10
        )
        
        bus.emit(event)
        
        assert len(events_received) == 1
        assert events_received[0].event_type == EventType.STOCK_INCREASED
    
    def test_subscribe_all(self):
        bus = EventBus()
        events_received = []
        
        def global_handler(event):
            events_received.append(event)
        
        bus.subscribe_all(global_handler)
        
        event1 = StockEvent(
            event_type=EventType.STOCK_INCREASED,
            monitor_config_id=1,
            product_id=123
        )
        
        event2 = StockEvent(
            event_type=EventType.STOCK_DECREASED,
            monitor_config_id=1,
            product_id=456
        )
        
        bus.emit(event1)
        bus.emit(event2)
        
        assert len(events_received) == 2
        assert events_received[0].event_type == EventType.STOCK_INCREASED
        assert events_received[1].event_type == EventType.STOCK_DECREASED
    
    def test_multiple_handlers(self):
        bus = EventBus()
        handler1_calls = []
        handler2_calls = []
        
        def handler1(event):
            handler1_calls.append(event)
        
        def handler2(event):
            handler2_calls.append(event)
        
        bus.subscribe(EventType.STOCK_INCREASED, handler1)
        bus.subscribe(EventType.STOCK_INCREASED, handler2)
        
        event = StockEvent(
            event_type=EventType.STOCK_INCREASED,
            monitor_config_id=1,
            product_id=123
        )
        
        bus.emit(event)
        
        assert len(handler1_calls) == 1
        assert len(handler2_calls) == 1
    
    def test_handler_error_does_not_stop_other_handlers(self):
        bus = EventBus()
        successful_handler_calls = []
        
        def failing_handler(event):
            raise Exception("Handler error")
        
        def successful_handler(event):
            successful_handler_calls.append(event)
        
        bus.subscribe(EventType.STOCK_INCREASED, failing_handler)
        bus.subscribe(EventType.STOCK_INCREASED, successful_handler)
        
        event = StockEvent(
            event_type=EventType.STOCK_INCREASED,
            monitor_config_id=1,
            product_id=123
        )
        
        bus.emit(event)
        
        assert len(successful_handler_calls) == 1
    
    def test_clear_handlers(self):
        bus = EventBus()
        events_received = []
        
        def handler(event):
            events_received.append(event)
        
        bus.subscribe(EventType.STOCK_INCREASED, handler)
        bus.clear_handlers()
        
        event = StockEvent(
            event_type=EventType.STOCK_INCREASED,
            monitor_config_id=1,
            product_id=123
        )
        
        bus.emit(event)
        
        assert len(events_received) == 0
