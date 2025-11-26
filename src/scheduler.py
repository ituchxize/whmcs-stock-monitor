import logging
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from pytz import timezone as pytz_timezone

from .monitoring_engine import MonitoringEngine
from .config import settings

logger = logging.getLogger(__name__)


class MonitorScheduler:
    def __init__(self, monitoring_engine: Optional[MonitoringEngine] = None):
        self.monitoring_engine = monitoring_engine or MonitoringEngine()
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._is_running = False
    
    def _create_scheduler(self) -> AsyncIOScheduler:
        tz = pytz_timezone(settings.monitor_timezone)
        scheduler = AsyncIOScheduler(timezone=tz)
        
        scheduler.add_listener(self._job_executed_listener, EVENT_JOB_EXECUTED)
        scheduler.add_listener(self._job_error_listener, EVENT_JOB_ERROR)
        
        return scheduler
    
    def _job_executed_listener(self, event) -> None:
        logger.info(f"Scheduled job executed successfully: {event.job_id}")
    
    def _job_error_listener(self, event) -> None:
        logger.error(f"Scheduled job error: {event.job_id}, exception: {event.exception}")
    
    def start(self) -> None:
        if self._is_running:
            logger.warning("Scheduler is already running")
            return
        
        logger.info("Starting monitoring scheduler")
        
        self.scheduler = self._create_scheduler()
        
        self.scheduler.add_job(
            func=self.monitoring_engine.run_monitoring_cycle,
            trigger=IntervalTrigger(seconds=settings.monitor_interval_seconds),
            id="stock_monitoring_job",
            name="Stock Monitoring Job",
            replace_existing=True,
            max_instances=1,
            coalesce=True
        )
        
        self.scheduler.start()
        self._is_running = True
        
        logger.info(
            f"Scheduler started with interval: {settings.monitor_interval_seconds} seconds, "
            f"timezone: {settings.monitor_timezone}"
        )
    
    def shutdown(self, wait: bool = True) -> None:
        if not self._is_running or not self.scheduler:
            logger.warning("Scheduler is not running")
            return
        
        logger.info("Shutting down monitoring scheduler")
        
        self.scheduler.shutdown(wait=wait)
        self._is_running = False
        
        logger.info("Scheduler shut down successfully")
    
    def is_running(self) -> bool:
        return self._is_running
    
    def get_jobs(self):
        if not self.scheduler:
            return []
        return self.scheduler.get_jobs()
    
    def pause(self) -> None:
        if self.scheduler:
            self.scheduler.pause()
            logger.info("Scheduler paused")
    
    def resume(self) -> None:
        if self.scheduler:
            self.scheduler.resume()
            logger.info("Scheduler resumed")
