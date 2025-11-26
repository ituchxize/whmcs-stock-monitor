from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    app_name: str = "WHMCS Stock Monitor"
    app_version: str = "1.0.0"
    debug: bool = False

    database_url: str = Field(
        default="sqlite+aiosqlite:///./whmcs_monitor.db",
        description="Async database URL (PostgreSQL or SQLite)"
    )

    whmcs_api_url: str = Field(
        default="",
        description="WHMCS API endpoint URL"
    )
    whmcs_api_identifier: str = Field(
        default="",
        description="WHMCS API identifier"
    )
    whmcs_api_secret: str = Field(
        default="",
        description="WHMCS API secret"
    )

    telegram_bot_token: Optional[str] = Field(
        default=None,
        description="Telegram bot token for notifications"
    )
    telegram_chat_id: Optional[str] = Field(
        default=None,
        description="Telegram chat ID for notifications"
    )

    monitoring_interval: int = Field(
        default=300,
        description="Monitoring interval in seconds"
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v:
            raise ValueError("database_url cannot be empty")
        return v


settings = Settings()
