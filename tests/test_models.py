import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models import MonitorConfig, StockRecord, Base


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


class TestMonitorConfig:
    def test_create_monitor_config(self, db_session):
        monitor = MonitorConfig(
            product_id=123,
            product_name="Test Product",
            is_active=True,
            threshold_low=5,
            threshold_high=50
        )
        
        db_session.add(monitor)
        db_session.commit()
        
        assert monitor.id is not None
        assert monitor.product_id == 123
        assert monitor.is_active is True
        assert monitor.threshold_low == 5
    
    def test_monitor_config_defaults(self, db_session):
        monitor = MonitorConfig(
            product_id=123
        )
        
        db_session.add(monitor)
        db_session.commit()
        
        assert monitor.is_active is True
        assert monitor.notify_on_restock is True
        assert monitor.notify_on_purchase is True
        assert monitor.notify_on_threshold is True
        assert monitor.created_at is not None
    
    def test_monitor_config_relationship(self, db_session):
        monitor = MonitorConfig(
            product_id=123,
            product_name="Test Product"
        )
        
        db_session.add(monitor)
        db_session.commit()
        
        record1 = StockRecord(
            monitor_config_id=monitor.id,
            quantity=10,
            delta=0
        )
        record2 = StockRecord(
            monitor_config_id=monitor.id,
            quantity=15,
            delta=5
        )
        
        db_session.add_all([record1, record2])
        db_session.commit()
        
        assert len(monitor.stock_records) == 2
    
    def test_monitor_config_unique_product_id(self, db_session):
        monitor1 = MonitorConfig(product_id=123)
        db_session.add(monitor1)
        db_session.commit()
        
        monitor2 = MonitorConfig(product_id=123)
        db_session.add(monitor2)
        
        with pytest.raises(Exception):
            db_session.commit()


class TestStockRecord:
    def test_create_stock_record(self, db_session):
        monitor = MonitorConfig(product_id=123)
        db_session.add(monitor)
        db_session.commit()
        
        record = StockRecord(
            monitor_config_id=monitor.id,
            quantity=10,
            delta=5,
            stock_control_enabled=True,
            available=True,
            change_type="restock"
        )
        
        db_session.add(record)
        db_session.commit()
        
        assert record.id is not None
        assert record.quantity == 10
        assert record.delta == 5
        assert record.change_type == "restock"
    
    def test_stock_record_defaults(self, db_session):
        monitor = MonitorConfig(product_id=123)
        db_session.add(monitor)
        db_session.commit()
        
        record = StockRecord(
            monitor_config_id=monitor.id,
            quantity=10
        )
        
        db_session.add(record)
        db_session.commit()
        
        assert record.delta == 0
        assert record.threshold_breached is False
        assert record.created_at is not None
    
    def test_stock_record_relationship(self, db_session):
        monitor = MonitorConfig(product_id=123)
        db_session.add(monitor)
        db_session.commit()
        
        record = StockRecord(
            monitor_config_id=monitor.id,
            quantity=10,
            delta=0
        )
        
        db_session.add(record)
        db_session.commit()
        
        assert record.monitor_config.product_id == 123
    
    def test_stock_record_cascade_delete(self, db_session):
        monitor = MonitorConfig(product_id=123)
        db_session.add(monitor)
        db_session.commit()
        
        record = StockRecord(
            monitor_config_id=monitor.id,
            quantity=10,
            delta=0
        )
        
        db_session.add(record)
        db_session.commit()
        
        record_id = record.id
        
        db_session.delete(monitor)
        db_session.commit()
        
        deleted_record = db_session.query(StockRecord).filter_by(id=record_id).first()
        assert deleted_record is None
    
    def test_threshold_breach_fields(self, db_session):
        monitor = MonitorConfig(product_id=123, threshold_low=5)
        db_session.add(monitor)
        db_session.commit()
        
        record = StockRecord(
            monitor_config_id=monitor.id,
            quantity=3,
            delta=-7,
            threshold_breached=True,
            threshold_type="low"
        )
        
        db_session.add(record)
        db_session.commit()
        
        assert record.threshold_breached is True
        assert record.threshold_type == "low"
