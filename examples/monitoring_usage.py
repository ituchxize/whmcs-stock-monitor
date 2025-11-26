"""
Example: Using the Monitoring Engine

This script demonstrates how to:
1. Set up monitor configurations
2. Subscribe to stock change events
3. Run monitoring cycles manually
4. Use the scheduler
"""

import logging
from datetime import datetime

from src import (
    MonitorConfig,
    StockRecord,
    MonitoringEngine,
    MonitorScheduler,
    event_bus,
    EventType,
    StockEvent
)
from src.database import get_db_context, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_monitor_configs():
    """Create sample monitor configurations."""
    with get_db_context() as db:
        monitor1 = MonitorConfig(
            product_id=123,
            product_name="VPS Hosting - Small",
            is_active=True,
            threshold_low=5,
            threshold_high=50,
            notify_on_restock=True,
            notify_on_purchase=True,
            notify_on_threshold=True
        )
        
        monitor2 = MonitorConfig(
            product_id=456,
            product_name="Dedicated Server",
            is_active=True,
            threshold_low=2,
            threshold_high=10,
            notify_on_restock=True,
            notify_on_purchase=True,
            notify_on_threshold=True
        )
        
        db.add_all([monitor1, monitor2])
        db.commit()
        
        logger.info(f"Created monitors: {monitor1.id}, {monitor2.id}")


def setup_event_handlers():
    """Set up event handlers for stock changes."""
    
    def handle_stock_increase(event: StockEvent):
        logger.info(
            f"🔼 RESTOCK DETECTED: {event.product_name} (ID: {event.product_id}) "
            f"increased by {event.delta} (now: {event.quantity})"
        )
    
    def handle_stock_decrease(event: StockEvent):
        logger.info(
            f"🔽 PURCHASE DETECTED: {event.product_name} (ID: {event.product_id}) "
            f"decreased by {abs(event.delta)} (now: {event.quantity})"
        )
    
    def handle_threshold_low(event: StockEvent):
        logger.warning(
            f"⚠️  LOW STOCK ALERT: {event.product_name} (ID: {event.product_id}) "
            f"is at {event.quantity} (threshold: {event.threshold_value})"
        )
    
    def handle_threshold_high(event: StockEvent):
        logger.info(
            f"📈 HIGH STOCK ALERT: {event.product_name} (ID: {event.product_id}) "
            f"is at {event.quantity} (threshold: {event.threshold_value})"
        )
    
    def handle_error(event: StockEvent):
        logger.error(
            f"❌ MONITOR ERROR: {event.product_name} (ID: {event.product_id}) "
            f"- {event.error_message}"
        )
    
    event_bus.subscribe(EventType.STOCK_INCREASED, handle_stock_increase)
    event_bus.subscribe(EventType.STOCK_DECREASED, handle_stock_decrease)
    event_bus.subscribe(EventType.THRESHOLD_BREACH_LOW, handle_threshold_low)
    event_bus.subscribe(EventType.THRESHOLD_BREACH_HIGH, handle_threshold_high)
    event_bus.subscribe(EventType.MONITOR_ERROR, handle_error)
    
    logger.info("Event handlers registered")


def run_manual_cycle():
    """Run a monitoring cycle manually."""
    logger.info("=== Running Manual Monitoring Cycle ===")
    
    engine = MonitoringEngine()
    results = engine.run_monitoring_cycle()
    
    logger.info(f"Cycle Results: {results}")
    
    with get_db_context() as db:
        records = db.query(StockRecord).order_by(StockRecord.created_at.desc()).limit(5).all()
        logger.info(f"Latest {len(records)} stock records:")
        for record in records:
            logger.info(
                f"  - Monitor {record.monitor_config_id}: "
                f"Qty={record.quantity}, Delta={record.delta}, Type={record.change_type}"
            )


def run_with_scheduler():
    """Run monitoring with scheduler."""
    logger.info("=== Starting Scheduler ===")
    
    scheduler = MonitorScheduler()
    scheduler.start()
    
    logger.info("Scheduler started. Press Ctrl+C to stop.")
    
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping scheduler...")
        scheduler.shutdown(wait=True)
        logger.info("Scheduler stopped")


def view_monitor_history(product_id: int):
    """View stock history for a product."""
    with get_db_context() as db:
        monitor = db.query(MonitorConfig).filter_by(product_id=product_id).first()
        
        if not monitor:
            logger.error(f"No monitor found for product {product_id}")
            return
        
        logger.info(f"Stock History for {monitor.product_name} (ID: {product_id})")
        logger.info("-" * 60)
        
        records = (
            db.query(StockRecord)
            .filter_by(monitor_config_id=monitor.id)
            .order_by(StockRecord.created_at.desc())
            .limit(10)
            .all()
        )
        
        for record in records:
            timestamp = record.created_at.strftime("%Y-%m-%d %H:%M:%S")
            delta_str = f"+{record.delta}" if record.delta > 0 else str(record.delta)
            breach_str = f" [THRESHOLD: {record.threshold_type}]" if record.threshold_breached else ""
            
            logger.info(
                f"{timestamp} | Qty: {record.quantity} | Delta: {delta_str} | "
                f"Type: {record.change_type}{breach_str}"
            )


if __name__ == "__main__":
    logger.info("WHMCS Stock Monitor - Example Usage")
    logger.info("=" * 60)
    
    init_db()
    logger.info("Database initialized")
    
    setup_monitor_configs()
    
    setup_event_handlers()
    
    logger.info("\nChoose an option:")
    logger.info("1. Run manual monitoring cycle")
    logger.info("2. Start scheduler (runs continuously)")
    logger.info("3. View product history")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        run_manual_cycle()
    elif choice == "2":
        run_with_scheduler()
    elif choice == "3":
        product_id = int(input("Enter product ID: ").strip())
        view_monitor_history(product_id)
    else:
        logger.error("Invalid choice")
