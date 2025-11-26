import pytest
from unittest.mock import Mock, patch
import time

from src.scheduler import MonitorScheduler
from src.monitoring_engine import MonitoringEngine


class TestMonitorScheduler:
    def test_scheduler_initialization(self):
        scheduler = MonitorScheduler()
        assert scheduler.monitoring_engine is not None
        assert scheduler.scheduler is None
        assert scheduler.is_running() is False
    
    def test_scheduler_start(self):
        mock_engine = Mock(spec=MonitoringEngine)
        scheduler = MonitorScheduler(monitoring_engine=mock_engine)
        
        try:
            scheduler.start()
            assert scheduler.is_running() is True
            assert scheduler.scheduler is not None
            
            jobs = scheduler.get_jobs()
            assert len(jobs) == 1
            assert jobs[0].id == "stock_monitoring_job"
        finally:
            scheduler.shutdown(wait=False)
    
    def test_scheduler_start_already_running(self):
        mock_engine = Mock(spec=MonitoringEngine)
        scheduler = MonitorScheduler(monitoring_engine=mock_engine)
        
        try:
            scheduler.start()
            scheduler.start()
            assert scheduler.is_running() is True
        finally:
            scheduler.shutdown(wait=False)
    
    def test_scheduler_shutdown(self):
        mock_engine = Mock(spec=MonitoringEngine)
        scheduler = MonitorScheduler(monitoring_engine=mock_engine)
        
        scheduler.start()
        assert scheduler.is_running() is True
        
        scheduler.shutdown(wait=False)
        assert scheduler.is_running() is False
    
    def test_scheduler_shutdown_not_running(self):
        mock_engine = Mock(spec=MonitoringEngine)
        scheduler = MonitorScheduler(monitoring_engine=mock_engine)
        
        scheduler.shutdown(wait=False)
        assert scheduler.is_running() is False
    
    def test_scheduler_pause_resume(self):
        mock_engine = Mock(spec=MonitoringEngine)
        scheduler = MonitorScheduler(monitoring_engine=mock_engine)
        
        try:
            scheduler.start()
            
            scheduler.pause()
            assert scheduler.scheduler.state == 2
            
            scheduler.resume()
            assert scheduler.scheduler.state == 1
        finally:
            scheduler.shutdown(wait=False)
    
    def test_get_jobs_no_scheduler(self):
        scheduler = MonitorScheduler()
        jobs = scheduler.get_jobs()
        assert jobs == []
    
    @patch('src.scheduler.settings')
    def test_scheduler_custom_interval(self, mock_settings):
        mock_settings.monitor_interval_seconds = 60
        mock_settings.monitor_timezone = "UTC"
        
        mock_engine = Mock(spec=MonitoringEngine)
        scheduler = MonitorScheduler(monitoring_engine=mock_engine)
        
        try:
            scheduler.start()
            
            jobs = scheduler.get_jobs()
            assert len(jobs) == 1
        finally:
            scheduler.shutdown(wait=False)
