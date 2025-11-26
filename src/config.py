import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./whmcs_monitor.db"
    
    whmcs_api_url: str = ""
    whmcs_api_identifier: str = ""
    whmcs_api_secret: str = ""
    whmcs_timeout: int = 30
    whmcs_cache_ttl: int = 300
    
    monitor_interval_seconds: int = 300
    monitor_timezone: str = "UTC"
    
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
