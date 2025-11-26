import pytest
from datetime import datetime
from sqlmodel import create_engine, Session, SQLModel, select

from src.models import Website, MonitorConfig, StockRecord, MonitorHistory


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()


class TestWebsite:
    def test_create_website(self, db_session):
        website = Website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret",
            region="US-East"
        )
        
        db_session.add(website)
        db_session.commit()
        
        assert website.id is not None
        assert website.name == "Test Website"
        assert website.is_active is True
        assert website.created_at is not None
    
    def test_website_defaults(self, db_session):
        website = Website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        )
        
        db_session.add(website)
        db_session.commit()
        
        assert website.is_active is True
        assert website.region is None
        assert website.created_at is not None
        assert website.updated_at is not None
    
    def test_website_relationship_with_monitors(self, db_session):
        website = Website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        )
        
        db_session.add(website)
        db_session.commit()
        
        monitor1 = MonitorConfig(website_id=website.id, product_id=101)
        monitor2 = MonitorConfig(website_id=website.id, product_id=102)
        
        db_session.add_all([monitor1, monitor2])
        db_session.commit()
        db_session.refresh(website)
        
        assert len(website.monitor_configs) == 2


class TestMonitorConfig:
    def test_create_monitor_config(self, db_session):
        website = Website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        )
        db_session.add(website)
        db_session.commit()
        
        monitor = MonitorConfig(
            website_id=website.id,
            product_id=123,
            product_name="Test Product",
            is_active=True,
            threshold_low=5,
            threshold_high=50,
            purchase_link="https://example.com/cart?pid=123"
        )
        
        db_session.add(monitor)
        db_session.commit()
        
        assert monitor.id is not None
        assert monitor.website_id == website.id
        assert monitor.product_id == 123
        assert monitor.is_active is True
        assert monitor.threshold_low == 5
        assert monitor.purchase_link == "https://example.com/cart?pid=123"
    
    def test_monitor_config_defaults(self, db_session):
        website = Website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        )
        db_session.add(website)
        db_session.commit()
        
        monitor = MonitorConfig(
            website_id=website.id,
            product_id=123
        )
        
        db_session.add(monitor)
        db_session.commit()
        
        assert monitor.is_active is True
        assert monitor.status == "active"
        assert monitor.notify_on_restock is True
        assert monitor.notify_on_purchase is True
        assert monitor.notify_on_threshold is True
        assert monitor.created_at is not None
    
    def test_monitor_config_relationship(self, db_session):
        website = Website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        )
        db_session.add(website)
        db_session.commit()
        
        monitor = MonitorConfig(
            website_id=website.id,
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
        db_session.refresh(monitor)
        
        assert len(monitor.stock_records) == 2
    
    def test_monitor_config_requires_website_id(self, db_session):
        monitor = MonitorConfig(
            website_id=999,
            product_id=123
        )
        
        db_session.add(monitor)
        
        with pytest.raises(Exception):
            db_session.commit()


class TestStockRecord:
    def test_create_stock_record(self, db_session):
        website = Website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        )
        db_session.add(website)
        db_session.commit()
        
        monitor = MonitorConfig(website_id=website.id, product_id=123)
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
        website = Website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        )
        db_session.add(website)
        db_session.commit()
        
        monitor = MonitorConfig(website_id=website.id, product_id=123)
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
        website = Website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        )
        db_session.add(website)
        db_session.commit()
        
        monitor = MonitorConfig(website_id=website.id, product_id=123)
        db_session.add(monitor)
        db_session.commit()
        
        record = StockRecord(
            monitor_config_id=monitor.id,
            quantity=10,
            delta=0
        )
        
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)
        
        assert record.monitor_config.product_id == 123
    
    def test_stock_record_cascade_delete(self, db_session):
        website = Website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        )
        db_session.add(website)
        db_session.commit()
        
        monitor = MonitorConfig(website_id=website.id, product_id=123)
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
        
        deleted_record = db_session.get(StockRecord, record_id)
        assert deleted_record is None
    
    def test_threshold_breach_fields(self, db_session):
        website = Website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        )
        db_session.add(website)
        db_session.commit()
        
        monitor = MonitorConfig(website_id=website.id, product_id=123, threshold_low=5)
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


class TestMonitorHistory:
    def test_create_monitor_history(self, db_session):
        website = Website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        )
        db_session.add(website)
        db_session.commit()
        
        monitor = MonitorConfig(website_id=website.id, product_id=123)
        db_session.add(monitor)
        db_session.commit()
        
        history = MonitorHistory(
            monitor_config_id=monitor.id,
            event_type="stock_increased",
            from_quantity=10,
            to_quantity=15,
            delta=5,
            change_type="restock",
            message="Stock replenished"
        )
        
        db_session.add(history)
        db_session.commit()
        
        assert history.id is not None
        assert history.event_type == "stock_increased"
        assert history.delta == 5
        assert history.message == "Stock replenished"
    
    def test_monitor_history_defaults(self, db_session):
        website = Website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        )
        db_session.add(website)
        db_session.commit()
        
        monitor = MonitorConfig(website_id=website.id, product_id=123)
        db_session.add(monitor)
        db_session.commit()
        
        history = MonitorHistory(
            monitor_config_id=monitor.id,
            event_type="monitor_started",
            to_quantity=0
        )
        
        db_session.add(history)
        db_session.commit()
        
        assert history.delta == 0
        assert history.threshold_breached is False
        assert history.created_at is not None
    
    def test_monitor_history_relationship(self, db_session):
        website = Website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        )
        db_session.add(website)
        db_session.commit()
        
        monitor = MonitorConfig(website_id=website.id, product_id=123)
        db_session.add(monitor)
        db_session.commit()
        
        history = MonitorHistory(
            monitor_config_id=monitor.id,
            event_type="stock_increased",
            to_quantity=15,
            delta=5
        )
        
        db_session.add(history)
        db_session.commit()
        db_session.refresh(history)
        
        assert history.monitor_config.product_id == 123
    
    def test_monitor_history_threshold_breach(self, db_session):
        website = Website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        )
        db_session.add(website)
        db_session.commit()
        
        monitor = MonitorConfig(
            website_id=website.id,
            product_id=123,
            threshold_low=5
        )
        db_session.add(monitor)
        db_session.commit()
        
        history = MonitorHistory(
            monitor_config_id=monitor.id,
            event_type="threshold_breach_low",
            from_quantity=10,
            to_quantity=3,
            delta=-7,
            threshold_breached=True,
            threshold_type="low",
            threshold_value=5,
            message="Stock below threshold"
        )
        
        db_session.add(history)
        db_session.commit()
        
        assert history.threshold_breached is True
        assert history.threshold_type == "low"
        assert history.threshold_value == 5
