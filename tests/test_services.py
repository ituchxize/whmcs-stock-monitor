import pytest
from sqlmodel import create_engine, Session, SQLModel

from src.models import Website, MonitorConfig
from src.services import WebsiteService, MonitorConfigService, MonitoringService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()


class TestWebsiteService:
    def test_create_website(self, db_session):
        service = WebsiteService(db_session)
        
        website = service.create_website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret",
            region="US-East"
        )
        
        assert website.id is not None
        assert website.name == "Test Website"
        assert website.region == "US-East"
    
    def test_create_duplicate_website_name(self, db_session):
        service = WebsiteService(db_session)
        
        service.create_website(
            name="Duplicate Name",
            website_url="https://test1.example.com",
            api_identifier="id1",
            api_secret="secret1"
        )
        
        with pytest.raises(ValueError, match="already exists"):
            service.create_website(
                name="Duplicate Name",
                website_url="https://test2.example.com",
                api_identifier="id2",
                api_secret="secret2"
            )
    
    def test_get_website(self, db_session):
        service = WebsiteService(db_session)
        created = service.create_website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        )
        
        found = service.get_website(created.id)
        
        assert found is not None
        assert found.id == created.id
    
    def test_update_website(self, db_session):
        service = WebsiteService(db_session)
        website = service.create_website(
            name="Original Name",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        )
        
        updated = service.update_website(
            website.id,
            name="Updated Name",
            region="EU-West"
        )
        
        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.region == "EU-West"
    
    def test_delete_website(self, db_session):
        service = WebsiteService(db_session)
        website = service.create_website(
            name="To Delete",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        )
        
        result = service.delete_website(website.id)
        
        assert result is True
        assert service.get_website(website.id) is None


class TestMonitorConfigService:
    def test_create_monitor(self, db_session):
        website_service = WebsiteService(db_session)
        website = website_service.create_website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        )
        
        monitor_service = MonitorConfigService(db_session)
        monitor = monitor_service.create_monitor(
            website_id=website.id,
            product_id=123,
            product_name="Test Product",
            threshold_low=5,
            threshold_high=50,
            purchase_link="https://test.example.com/cart?pid=123"
        )
        
        assert monitor.id is not None
        assert monitor.website_id == website.id
        assert monitor.product_id == 123
        assert monitor.purchase_link == "https://test.example.com/cart?pid=123"
    
    def test_create_monitor_invalid_website(self, db_session):
        monitor_service = MonitorConfigService(db_session)
        
        with pytest.raises(ValueError, match="does not exist"):
            monitor_service.create_monitor(
                website_id=999,
                product_id=123
            )
    
    def test_create_duplicate_monitor(self, db_session):
        website_service = WebsiteService(db_session)
        website = website_service.create_website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        )
        
        monitor_service = MonitorConfigService(db_session)
        monitor_service.create_monitor(
            website_id=website.id,
            product_id=123
        )
        
        with pytest.raises(ValueError, match="already exists"):
            monitor_service.create_monitor(
                website_id=website.id,
                product_id=123
            )
    
    def test_get_active_monitors_by_website(self, db_session):
        website_service = WebsiteService(db_session)
        website1 = website_service.create_website(
            name="Website 1",
            website_url="https://test1.example.com",
            api_identifier="id1",
            api_secret="secret1"
        )
        website2 = website_service.create_website(
            name="Website 2",
            website_url="https://test2.example.com",
            api_identifier="id2",
            api_secret="secret2"
        )
        
        monitor_service = MonitorConfigService(db_session)
        monitor_service.create_monitor(website_id=website1.id, product_id=101, is_active=True)
        monitor_service.create_monitor(website_id=website1.id, product_id=102, is_active=False)
        monitor_service.create_monitor(website_id=website2.id, product_id=201, is_active=True)
        
        website1_monitors = monitor_service.get_active_monitors(website_id=website1.id)
        all_monitors = monitor_service.get_active_monitors()
        
        assert len(website1_monitors) == 1
        assert website1_monitors[0].product_id == 101
        assert len(all_monitors) == 2
    
    def test_update_monitor(self, db_session):
        website_service = WebsiteService(db_session)
        website = website_service.create_website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        )
        
        monitor_service = MonitorConfigService(db_session)
        monitor = monitor_service.create_monitor(
            website_id=website.id,
            product_id=123,
            threshold_low=5
        )
        
        updated = monitor_service.update_monitor(
            monitor.id,
            threshold_low=10,
            threshold_high=100,
            status="paused"
        )
        
        assert updated is not None
        assert updated.threshold_low == 10
        assert updated.threshold_high == 100
        assert updated.status == "paused"


class TestMonitoringService:
    def test_record_stock_change(self, db_session):
        website_service = WebsiteService(db_session)
        website = website_service.create_website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        )
        
        monitor_service = MonitorConfigService(db_session)
        monitor = monitor_service.create_monitor(
            website_id=website.id,
            product_id=123
        )
        
        monitoring_service = MonitoringService(db_session)
        record = monitoring_service.record_stock_change(
            monitor_config_id=monitor.id,
            quantity=10,
            delta=5,
            change_type="restock"
        )
        
        assert record.id is not None
        assert record.quantity == 10
        assert record.delta == 5
        assert record.change_type == "restock"
    
    def test_record_history(self, db_session):
        website_service = WebsiteService(db_session)
        website = website_service.create_website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        )
        
        monitor_service = MonitorConfigService(db_session)
        monitor = monitor_service.create_monitor(
            website_id=website.id,
            product_id=123
        )
        
        monitoring_service = MonitoringService(db_session)
        history = monitoring_service.record_history(
            monitor_config_id=monitor.id,
            event_type="stock_increased",
            from_quantity=5,
            to_quantity=10,
            delta=5,
            change_type="restock",
            message="Stock replenished"
        )
        
        assert history.id is not None
        assert history.event_type == "stock_increased"
        assert history.message == "Stock replenished"
    
    def test_get_status_summary(self, db_session):
        website_service = WebsiteService(db_session)
        website = website_service.create_website(
            name="Test Website",
            website_url="https://test.example.com",
            api_identifier="test_id",
            api_secret="test_secret"
        )
        
        monitor_service = MonitorConfigService(db_session)
        monitor = monitor_service.create_monitor(
            website_id=website.id,
            product_id=123,
            product_name="Test Product"
        )
        
        monitoring_service = MonitoringService(db_session)
        monitoring_service.record_stock_change(
            monitor_config_id=monitor.id,
            quantity=10,
            delta=0,
            change_type="initial"
        )
        monitoring_service.record_history(
            monitor_config_id=monitor.id,
            event_type="monitor_started",
            to_quantity=10,
            delta=0
        )
        
        summary = monitoring_service.get_status_summary(monitor.id)
        
        assert summary["monitor_id"] == monitor.id
        assert summary["website_id"] == website.id
        assert summary["product_id"] == 123
        assert summary["product_name"] == "Test Product"
        assert summary["current_quantity"] == 10
        assert summary["recent_events"] == 1


class TestMultiWebsiteScenarios:
    def test_multiple_websites_with_distinct_credentials(self, db_session):
        service = WebsiteService(db_session)
        
        website1 = service.create_website(
            name="Main Site",
            website_url="https://main.example.com",
            api_identifier="main_id",
            api_secret="main_secret",
            region="US-East"
        )
        
        website2 = service.create_website(
            name="EU Site",
            website_url="https://eu.example.com",
            api_identifier="eu_id",
            api_secret="eu_secret",
            region="EU-West"
        )
        
        assert website1.api_identifier != website2.api_identifier
        assert website1.api_secret != website2.api_secret
        assert website1.region != website2.region
    
    def test_monitors_require_valid_website_id(self, db_session):
        monitor_service = MonitorConfigService(db_session)
        
        with pytest.raises(ValueError, match="does not exist"):
            monitor_service.create_monitor(
                website_id=999,
                product_id=123
            )
    
    def test_same_product_different_websites(self, db_session):
        website_service = WebsiteService(db_session)
        website1 = website_service.create_website(
            name="Website 1",
            website_url="https://test1.example.com",
            api_identifier="id1",
            api_secret="secret1"
        )
        website2 = website_service.create_website(
            name="Website 2",
            website_url="https://test2.example.com",
            api_identifier="id2",
            api_secret="secret2"
        )
        
        monitor_service = MonitorConfigService(db_session)
        monitor1 = monitor_service.create_monitor(
            website_id=website1.id,
            product_id=123,
            product_name="VPS Hosting"
        )
        monitor2 = monitor_service.create_monitor(
            website_id=website2.id,
            product_id=123,
            product_name="VPS Hosting"
        )
        
        assert monitor1.product_id == monitor2.product_id
        assert monitor1.website_id != monitor2.website_id
        assert monitor1.id != monitor2.id
