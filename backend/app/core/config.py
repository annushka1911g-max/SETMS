"""
SETMS Backend — Application Settings
Uses Pydantic Settings v2 to read from environment variables and .env files.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Application ----
    app_env: Literal["development", "production", "testing"] = "development"
    app_debug: bool = True
    app_secret_key: str = "dev_secret_CHANGE_IN_PRODUCTION"
    app_allowed_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"]
    )

    @field_validator("app_allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # ---- JWT ----
    jwt_secret_key: str = "dev_jwt_secret_CHANGE_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # ---- Database ----
    database_url: str = "sqlite+aiosqlite:///./setms_dev.db"

    # ---- Redis ----
    redis_url: str = "redis://localhost:6379/0"

    # ---- MQTT ----
    mqtt_broker_host: str = "localhost"
    mqtt_broker_port: int = 1883
    mqtt_username: str = "setms_backend"
    mqtt_password: str = "setms_dev_pass"
    mqtt_client_id: str = "setms-backend-001"
    mqtt_topic_prefix: str = "setms/v1"
    mqtt_use_tls: bool = False
    mqtt_ca_cert_path: str = ""

    # ---- AI Engine ----
    ai_engine_url: str = "http://localhost:8001"
    ai_engine_api_key: str = ""
    ai_simulation_mode: bool = True

    # ---- Routing ----
    routing_provider: Literal["local", "osrm"] = "local"
    osrm_base_url: str = "http://router.project-osrm.org"

    # ---- Email ----
    notify_email_enabled: bool = False
    smtp_host: str = "smtp.example.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_address: str = "setms@example.com"

    # ---- Seed Accounts ----
    seed_admin_email: str = "admin@setms.org"
    seed_admin_password: str = "Admin1234!"
    seed_operator_email: str = "operator@setms.org"
    seed_operator_password: str = "Operator1234!"
    seed_driver_email: str = "driver@setms.org"
    seed_driver_password: str = "Driver1234!"
    seed_hospital_email: str = "hospital@setms.org"
    seed_hospital_password: str = "Hospital1234!"

    # ---- Logging ----
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["json", "text"] = "json"

    # ---- Rate Limiting ----
    rate_limit_per_minute: int = 60
    auth_rate_limit_per_minute: int = 10

    # ---- Computed helpers ----
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_testing(self) -> bool:
        return self.app_env == "testing"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()
