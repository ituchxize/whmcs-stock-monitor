import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.monitoring_engine import MonitoringEngine, StockChangeDetector
from src.models import MonitorConfig, StockRecord, Base
from src.events import EventType, event_bus


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def mock_whmcs_client():
    client = Mock()
    client.get_product_inventory = Mock(return_value={
        'product_id': 123,
        'name': 'Test Product',
        'stock_control': True,
        'quantity': 10,
        'available': True,
        'last_updated': datetime.utcnow().isoformat()
    })
    return client


@pytest.fixture
def sample_monitor(db_session):
    monitor = MonitorConfig(
        product_id=123,
        product_name="Test Product",
        is_active=True,
        threshold_low=5,
        threshold_high=50,
        notify_on_restock=True,
        notify_on_purchase=True,
        notify_on_threshold=True
    )
    db_session.add(monitor)
    db_session.commit()
    return monitor


class TestStockChangeDetector:
    def test_detect_initial_change(self):
        detector = StockChangeDetector()
        change_type = detector.detect_change_type(10, None, 0)
        assert change_type == "initial"
    
    def test_detect_restock(self):
        detector = StockChangeDetector()
        change_type = detector.detect_change_type(15, 10, 5)
        assert change_type == "restock"
    
    def test_detect_purchase(self):
        detector = StockChangeDetector()
        change_type = detector.detect_change_type(8, 10, -2)
        assert change_type == "purchase"
    
    def test_detect_unchanged(self):
        detector = StockChangeDetector()
        change_type = detector.detect_change_type(10, 10, 0)
        assert change_type == "unchanged"
    
    def test_check_threshold_low_breach(self):
        detector = StockChangeDetector()
        breached, threshold_type = detector.check_threshold_breach(3, 5, 50)
        assert breached is True
        assert threshold_type == "low"
    
    def test_check_threshold_high_breach(self):
        detector = StockChangeDetector()
        breached, threshold_type = detector.check_threshold_breach(55, 5, 50)
        assert breached is True
        assert threshold_type == "high"
    
    def test_check_threshold_no_breach(self):
        detector = StockChangeDetector()
        breached, threshold_type = detector.check_threshold_breach(25, 5, 50)
        assert breached is False
        assert threshold_type is None
    
    def test_check_threshold_no_thresholds_set(self):
        detector = StockChangeDetector()
        breached, threshold_type = detector.check_threshold_breach(100, None, None)
        assert breached is False
        assert threshold_type is None


class TestMonitoringEngine:
    def test_get_active_monitors(self, db_session, sample_monitor):
        engine = MonitoringEngine()
        monitors = engine._get_active_monitors(db_session)
        assert len(monitors) == 1
        assert monitors[0].product_id == 123
    
    def test_get_active_monitors_filters_inactive(self, db_session, sample_monitor):
        inactive_monitor = MonitorConfig(
            product_id=456,
            product_name="Inactive Product",
            is_active=False
        )
        db_session.add(inactive_monitor)
        db_session.commit()
        
        engine = MonitoringEngine()
        monitors = engine._get_active_monitors(db_session)
        assert len(monitors) == 1
        assert monitors[0].product_id == 123
    
    def test_get_latest_stock_record(self, db_session, sample_monitor):
        record1 = StockRecord(
            monitor_config_id=sample_monitor.id,
            quantity=10,
            delta=0,
            change_type="initial"
        )
        record2 = StockRecord(
            monitor_config_id=sample_monitor.id,
            quantity=15,
            delta=5,
            change_type="restock"
        )
        db_session.add_all([record1, record2])
        db_session.commit()
        
        engine = MonitoringEngine()
        latest = engine._get_latest_stock_record(db_session, sample_monitor.id)
        assert latest.quantity == 15
        assert latest.delta == 5
    
    def test_check_monitor_first_time(self, db_session, sample_monitor, mock_whmcs_client):
        engine = MonitoringEngine(whmcs_client=mock_whmcs_client)
        
        record_created, change_detected, threshold_breached = engine._check_monitor(
            db_session, sample_monitor, mock_whmcs_client
        )
        
        assert record_created is True
        assert change_detected is False
        assert threshold_breached is False
        
        records = db_session.query(StockRecord).filter_by(monitor_config_id=sample_monitor.id).all()
        assert len(records) == 1
        assert records[0].quantity == 10
        assert records[0].delta == 0
        assert records[0].change_type == "initial"
    
    def test_check_monitor_stock_increase(self, db_session, sample_monitor, mock_whmcs_client):
        initial_record = StockRecord(
            monitor_config_id=sample_monitor.id,
            quantity=10,
            delta=0,
            change_type="initial"
        )
        db_session.add(initial_record)
        db_session.commit()
        
        mock_whmcs_client.get_product_inventory.return_value = {
            'product_id': 123,
            'name': 'Test Product',
            'stock_control': True,
            'quantity': 20,
            'available': True,
            'last_updated': datetime.utcnow().isoformat()
        }
        
        engine = MonitoringEngine(whmcs_client=mock_whmcs_client)
        
        record_created, change_detected, threshold_breached = engine._check_monitor(
            db_session, sample_monitor, mock_whmcs_client
        )
        
        assert record_created is True
        assert change_detected is True
        assert threshold_breached is False
        
        records = db_session.query(StockRecord).filter_by(monitor_config_id=sample_monitor.id).order_by(StockRecord.created_at).all()
        assert len(records) == 2
        assert records[1].quantity == 20
        assert records[1].delta == 10
        assert records[1].change_type == "restock"
    
    def test_check_monitor_stock_decrease(self, db_session, sample_monitor, mock_whmcs_client):
        initial_record = StockRecord(
            monitor_config_id=sample_monitor.id,
            quantity=10,
            delta=0,
            change_type="initial"
        )
        db_session.add(initial_record)
        db_session.commit()
        
        mock_whmcs_client.get_product_inventory.return_value = {
            'product_id': 123,
            'name': 'Test Product',
            'stock_control': True,
            'quantity': 7,
            'available': True,
            'last_updated': datetime.utcnow().isoformat()
        }
        
        engine = MonitoringEngine(whmcs_client=mock_whmcs_client)
        
        record_created, change_detected, threshold_breached = engine._check_monitor(
            db_session, sample_monitor, mock_whmcs_client
        )
        
        assert record_created is True
        assert change_detected is True
        
        records = db_session.query(StockRecord).filter_by(monitor_config_id=sample_monitor.id).order_by(StockRecord.created_at).all()
        assert len(records) == 2
        assert records[1].quantity == 7
        assert records[1].delta == -3
        assert records[1].change_type == "purchase"
    
    def test_check_monitor_threshold_breach_low(self, db_session, sample_monitor, mock_whmcs_client):
        initial_record = StockRecord(
            monitor_config_id=sample_monitor.id,
            quantity=10,
            delta=0,
            change_type="initial"
        )
        db_session.add(initial_record)
        db_session.commit()
        
        mock_whmcs_client.get_product_inventory.return_value = {
            'product_id': 123,
            'name': 'Test Product',
            'stock_control': True,
            'quantity': 3,
            'available': True,
            'last_updated': datetime.utcnow().isoformat()
        }
        
        engine = MonitoringEngine(whmcs_client=mock_whmcs_client)
        
        record_created, change_detected, threshold_breached = engine._check_monitor(
            db_session, sample_monitor, mock_whmcs_client
        )
        
        assert record_created is True
        assert change_detected is True
        assert threshold_breached is True
        
        records = db_session.query(StockRecord).filter_by(monitor_config_id=sample_monitor.id).order_by(StockRecord.created_at).all()
        assert len(records) == 2
        assert records[1].quantity == 3
        assert records[1].threshold_breached is True
        assert records[1].threshold_type == "low"
    
    def test_check_monitor_threshold_breach_high(self, db_session, sample_monitor, mock_whmcs_client):
        initial_record = StockRecord(
            monitor_config_id=sample_monitor.id,
            quantity=10,
            delta=0,
            change_type="initial"
        )
        db_session.add(initial_record)
        db_session.commit()
        
        mock_whmcs_client.get_product_inventory.return_value = {
            'product_id': 123,
            'name': 'Test Product',
            'stock_control': True,
            'quantity': 55,
            'available': True,
            'last_updated': datetime.utcnow().isoformat()
        }
        
        engine = MonitoringEngine(whmcs_client=mock_whmcs_client)
        
        record_created, change_detected, threshold_breached = engine._check_monitor(
            db_session, sample_monitor, mock_whmcs_client
        )
        
        assert record_created is True
        assert threshold_breached is True
        
        records = db_session.query(StockRecord).filter_by(monitor_config_id=sample_monitor.id).order_by(StockRecord.created_at).all()
        assert len(records) == 2
        assert records[1].quantity == 55
        assert records[1].threshold_breached is True
        assert records[1].threshold_type == "high"
    
    @patch('src.monitoring_engine.get_db_context')
    def test_run_monitoring_cycle(self, mock_get_db_context, db_session, sample_monitor, mock_whmcs_client):
        mock_get_db_context.return_value.__enter__ = Mock(return_value=db_session)
        mock_get_db_context.return_value.__exit__ = Mock(return_value=False)
        
        engine = MonitoringEngine(whmcs_client=mock_whmcs_client)
        
        results = engine.run_monitoring_cycle()
        
        assert results["monitors_checked"] == 1
        assert results["records_created"] == 1
        assert results["errors"] == 0
        assert "started_at" in results
        assert "completed_at" in results
    
    @patch('src.monitoring_engine.get_db_context')
    def test_run_monitoring_cycle_with_error(self, mock_get_db_context, db_session, sample_monitor):
        mock_get_db_context.return_value.__enter__ = Mock(return_value=db_session)
        mock_get_db_context.return_value.__exit__ = Mock(return_value=False)
        
        mock_whmcs_client = Mock()
        mock_whmcs_client.get_product_inventory = Mock(side_effect=Exception("API Error"))
        
        engine = MonitoringEngine(whmcs_client=mock_whmcs_client)
        
        results = engine.run_monitoring_cycle()
        
        assert results["monitors_checked"] == 1
        assert results["errors"] == 1
    
    def test_emit_events_stock_increase(self, sample_monitor, mock_whmcs_client):
        engine = MonitoringEngine(whmcs_client=mock_whmcs_client)
        
        record = StockRecord(
            monitor_config_id=sample_monitor.id,
            quantity=20,
            delta=10,
            change_type="restock",
            threshold_breached=False
        )
        
        events_emitted = []
        
        def capture_event(event):
            events_emitted.append(event)
        
        event_bus.subscribe(EventType.STOCK_INCREASED, capture_event)
        
        engine._emit_events(sample_monitor, record, 10)
        
        event_bus._handlers[EventType.STOCK_INCREASED].remove(capture_event)
        
        assert len(events_emitted) > 0
        assert events_emitted[0].event_type == EventType.STOCK_INCREASED
        assert events_emitted[0].delta == 10
    
    def test_emit_events_threshold_breach(self, sample_monitor, mock_whmcs_client):
        engine = MonitoringEngine(whmcs_client=mock_whmcs_client)
        
        record = StockRecord(
            monitor_config_id=sample_monitor.id,
            quantity=3,
            delta=-7,
            change_type="purchase",
            threshold_breached=True,
            threshold_type="low"
        )
        
        events_emitted = []
        
        def capture_event(event):
            events_emitted.append(event)
        
        event_bus.subscribe(EventType.THRESHOLD_BREACH_LOW, capture_event)
        
        engine._emit_events(sample_monitor, record, 10)
        
        event_bus._handlers[EventType.THRESHOLD_BREACH_LOW].remove(capture_event)
        
        threshold_events = [e for e in events_emitted if e.event_type == EventType.THRESHOLD_BREACH_LOW]
        assert len(threshold_events) > 0
        assert threshold_events[0].threshold_type == "low"
        assert threshold_events[0].threshold_value == 5
