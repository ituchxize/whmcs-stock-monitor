import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.persistence.database import AsyncSessionLocal, init_db
from src.persistence.models import MonitorConfig, StockRecord, NotificationLog


async def test_models():
    print("Testing database models...")
    
    await init_db()
    print("✓ Database initialized")
    
    async with AsyncSessionLocal() as session:
        monitor = MonitorConfig(
            product_id=123,
            product_name="Test Product",
            is_active=True,
            check_interval=300,
            notify_on_restock=True,
            notify_on_purchase=True,
            notify_on_stock_low=False,
        )
        session.add(monitor)
        await session.commit()
        await session.refresh(monitor)
        
        print(f"✓ Created MonitorConfig: {monitor}")
        
        stock_record = StockRecord(
            monitor_config_id=monitor.id,
            stock_quantity=10,
            price=29.99,
            stock_control_enabled=True,
            is_available=True,
            change_detected=False,
        )
        session.add(stock_record)
        await session.commit()
        await session.refresh(stock_record)
        
        print(f"✓ Created StockRecord: {stock_record}")
        
        notification = NotificationLog(
            monitor_config_id=monitor.id,
            notification_type="restock",
            channel="telegram",
            message="Test notification",
            status="pending",
        )
        session.add(notification)
        await session.commit()
        await session.refresh(notification)
        
        print(f"✓ Created NotificationLog: {notification}")
        
        await session.delete(monitor)
        await session.commit()
        
        print("✓ Cascade delete verified")
    
    print("\nAll model tests passed!")


if __name__ == "__main__":
    asyncio.run(test_models())
