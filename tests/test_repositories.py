import pytest
from datetime import datetime
from sqlmodel import create_engine, Session, SQLModel

from src.models import Website, MonitorConfig, StockRecord, MonitorHistory
from src.repositories import (
    WebsiteRepository,
    MonitorConfigRepository,
    StockRecordRepository,
    MonitorHistoryRepository
)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()


class TestWebsiteRepository:
    def test_create_website(self, db_session):
        repo = WebsiteRepository(db_session)
        website = Website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret",
            region="US-East"
        )
        
        created = repo.create(website)
        
        assert created.id is not None
        assert created.name == "Test Website"
        assert created.website_url == "https://test.example.com"
        assert created.is_active is True
        assert created.created_at is not None
    
    def test_get_by_id(self, db_session):
        repo = WebsiteRepository(db_session)
        website = Website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        )
        created = repo.create(website)
        
        found = repo.get_by_id(created.id)
        
        assert found is not None
        assert found.id == created.id
        assert found.name == "Test Website"
    
    def test_get_by_name(self, db_session):
        repo = WebsiteRepository(db_session)
        website = Website(
            name="Unique Name",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        )
        repo.create(website)
        
        found = repo.get_by_name("Unique Name")
        
        assert found is not None
        assert found.name == "Unique Name"
    
    def test_get_all(self, db_session):
        repo = WebsiteRepository(db_session)
        website1 = Website(
            name="Website 1",
            website_url="https://test1.example.com",
            api_identifier="id1",
            api_secret="secret1"
        )
        website2 = Website(
            name="Website 2",
            website_url="https://test2.example.com",
            api_identifier="id2",
            api_secret="secret2",
            is_active=False
        )
        repo.create(website1)
        repo.create(website2)
        
        all_websites = repo.get_all()
        active_websites = repo.get_all(active_only=True)
        
        assert len(all_websites) == 2
        assert len(active_websites) == 1
        assert active_websites[0].name == "Website 1"
    
    def test_update_website(self, db_session):
        repo = WebsiteRepository(db_session)
        website = Website(
            name="Original Name",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        )
        created = repo.create(website)
        
        created.name = "Updated Name"
        updated = repo.update(created)
        
        assert updated.name == "Updated Name"
        assert updated.updated_at > created.created_at
    
    def test_delete_website(self, db_session):
        repo = WebsiteRepository(db_session)
        website = Website(
            name="To Delete",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        )
        created = repo.create(website)
        
        result = repo.delete(created.id)
        found = repo.get_by_id(created.id)
        
        assert result is True
        assert found is None


class TestMonitorConfigRepository:
    def test_create_monitor_config(self, db_session):
        website_repo = WebsiteRepository(db_session)
        website = website_repo.create(Website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        ))
        
        repo = MonitorConfigRepository(db_session)
        monitor = MonitorConfig(
            website_id=website.id,
            product_id=123,
            product_name="Test Product",
            threshold_low=5,
            threshold_high=50
        )
        
        created = repo.create(monitor)
        
        assert created.id is not None
        assert created.website_id == website.id
        assert created.product_id == 123
        assert created.is_active is True
    
    def test_get_by_website_and_product(self, db_session):
        website_repo = WebsiteRepository(db_session)
        website = website_repo.create(Website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        ))
        
        repo = MonitorConfigRepository(db_session)
        monitor = repo.create(MonitorConfig(
            website_id=website.id,
            product_id=123
        ))
        
        found = repo.get_by_website_and_product(website.id, 123)
        
        assert found is not None
        assert found.id == monitor.id
    
    def test_get_active_by_website(self, db_session):
        website_repo = WebsiteRepository(db_session)
        website = website_repo.create(Website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        ))
        
        repo = MonitorConfigRepository(db_session)
        repo.create(MonitorConfig(website_id=website.id, product_id=101, is_active=True))
        repo.create(MonitorConfig(website_id=website.id, product_id=102, is_active=False))
        repo.create(MonitorConfig(website_id=website.id, product_id=103, is_active=True))
        
        active_monitors = repo.get_active_by_website(website.id)
        
        assert len(active_monitors) == 2
        assert all(m.is_active for m in active_monitors)
    
    def test_get_all_active(self, db_session):
        website_repo = WebsiteRepository(db_session)
        website1 = website_repo.create(Website(
            name="Website 1",
            website_url="https://test1.example.com",
            api_identifier="id1",
            api_secret="secret1"
        ))
        website2 = website_repo.create(Website(
            name="Website 2",
            website_url="https://test2.example.com",
            api_identifier="id2",
            api_secret="secret2"
        ))
        
        repo = MonitorConfigRepository(db_session)
        repo.create(MonitorConfig(website_id=website1.id, product_id=101, is_active=True))
        repo.create(MonitorConfig(website_id=website1.id, product_id=102, is_active=False))
        repo.create(MonitorConfig(website_id=website2.id, product_id=201, is_active=True))
        
        all_active = repo.get_all_active()
        
        assert len(all_active) == 2
        assert all(m.is_active for m in all_active)


class TestStockRecordRepository:
    def test_create_stock_record(self, db_session):
        website_repo = WebsiteRepository(db_session)
        website = website_repo.create(Website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        ))
        
        monitor_repo = MonitorConfigRepository(db_session)
        monitor = monitor_repo.create(MonitorConfig(
            website_id=website.id,
            product_id=123
        ))
        
        repo = StockRecordRepository(db_session)
        record = StockRecord(
            monitor_config_id=monitor.id,
            quantity=10,
            delta=5,
            change_type="restock"
        )
        
        created = repo.create(record)
        
        assert created.id is not None
        assert created.quantity == 10
        assert created.delta == 5
    
    def test_get_latest_by_monitor(self, db_session):
        website_repo = WebsiteRepository(db_session)
        website = website_repo.create(Website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        ))
        
        monitor_repo = MonitorConfigRepository(db_session)
        monitor = monitor_repo.create(MonitorConfig(
            website_id=website.id,
            product_id=123
        ))
        
        repo = StockRecordRepository(db_session)
        repo.create(StockRecord(monitor_config_id=monitor.id, quantity=10, delta=0))
        repo.create(StockRecord(monitor_config_id=monitor.id, quantity=15, delta=5))
        latest = repo.create(StockRecord(monitor_config_id=monitor.id, quantity=12, delta=-3))
        
        found = repo.get_latest_by_monitor(monitor.id)
        
        assert found is not None
        assert found.id == latest.id
        assert found.quantity == 12


class TestMonitorHistoryRepository:
    def test_create_history(self, db_session):
        website_repo = WebsiteRepository(db_session)
        website = website_repo.create(Website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        ))
        
        monitor_repo = MonitorConfigRepository(db_session)
        monitor = monitor_repo.create(MonitorConfig(
            website_id=website.id,
            product_id=123
        ))
        
        repo = MonitorHistoryRepository(db_session)
        history = MonitorHistory(
            monitor_config_id=monitor.id,
            event_type="stock_increased",
            from_quantity=10,
            to_quantity=15,
            delta=5,
            change_type="restock"
        )
        
        created = repo.create(history)
        
        assert created.id is not None
        assert created.event_type == "stock_increased"
        assert created.delta == 5
    
    def test_get_by_monitor(self, db_session):
        website_repo = WebsiteRepository(db_session)
        website = website_repo.create(Website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        ))
        
        monitor_repo = MonitorConfigRepository(db_session)
        monitor = monitor_repo.create(MonitorConfig(
            website_id=website.id,
            product_id=123
        ))
        
        repo = MonitorHistoryRepository(db_session)
        repo.create(MonitorHistory(
            monitor_config_id=monitor.id,
            event_type="stock_increased",
            to_quantity=10,
            delta=5
        ))
        repo.create(MonitorHistory(
            monitor_config_id=monitor.id,
            event_type="stock_decreased",
            to_quantity=5,
            delta=-5
        ))
        
        history = repo.get_by_monitor(monitor.id)
        
        assert len(history) == 2
    
    def test_get_by_event_type(self, db_session):
        website_repo = WebsiteRepository(db_session)
        website = website_repo.create(Website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        ))
        
        monitor_repo = MonitorConfigRepository(db_session)
        monitor = monitor_repo.create(MonitorConfig(
            website_id=website.id,
            product_id=123
        ))
        
        repo = MonitorHistoryRepository(db_session)
        repo.create(MonitorHistory(
            monitor_config_id=monitor.id,
            event_type="stock_increased",
            to_quantity=10,
            delta=5
        ))
        repo.create(MonitorHistory(
            monitor_config_id=monitor.id,
            event_type="threshold_breach",
            to_quantity=2,
            delta=-8
        ))
        repo.create(MonitorHistory(
            monitor_config_id=monitor.id,
            event_type="stock_increased",
            to_quantity=15,
            delta=13
        ))
        
        increased = repo.get_by_event_type("stock_increased")
        
        assert len(increased) == 2
        assert all(h.event_type == "stock_increased" for h in increased)
