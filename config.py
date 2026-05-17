from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = Field(alias="BOT_TOKEN")
    admin_id: int = Field(default=0, alias="ADMIN_ID")
    start_image_url: str = Field(
        default="app/assets/welcome.png",
        alias="START_IMAGE_URL",
    )
    support_manager_url: str = Field(default="https://t.me/support", alias="SUPPORT_MANAGER_URL")
    manager_username: str = Field(default="https://t.me/support", alias="MANAGER_USERNAME")

    fsm_storage: str = Field(default="memory", alias="FSM_STORAGE")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    database_url: str = Field(
        default="postgresql+asyncpg://tg_star:tg_star_password@localhost:5432/tg_star",
        alias="DATABASE_URL",
    )

    admin_owner_ids_raw: str = Field(default="", alias="ADMIN_OWNER_IDS")
    admin_manager_ids_raw: str = Field(default="", alias="ADMIN_MANAGER_IDS")

    cryptobot_api_token: str = Field(default="", alias="CRYPTOBOT_API_TOKEN")
    cryptobot_webhook_secret: str = Field(default="", alias="CRYPTOBOT_WEBHOOK_SECRET")

    referrals_enabled: bool = Field(default=False, alias="REFERRALS_ENABLED")
    referral_percent: int = Field(default=70, alias="REFERRAL_PERCENT")
    referral_base: str = Field(default="profit", alias="REFERRAL_BASE")

    http_timeout: float = Field(default=15.0, alias="HTTP_TIMEOUT")
    http_retry_attempts: int = Field(default=3, alias="HTTP_RETRY_ATTEMPTS")
    http_retry_delay: float = Field(default=0.5, alias="HTTP_RETRY_DELAY")

    polling_retry_delay: float = Field(default=10.0, alias="POLLING_RETRY_DELAY")

    @field_validator("fsm_storage", mode="before")
    @classmethod
    def normalize_fsm_storage(cls, value: Any) -> str:
        return str(value or "memory").lower()

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: Any) -> str:
        return str(value or "INFO").upper()

    @property
    def admin_owner_ids(self) -> tuple[int, ...]:
        return self._parse_admin_ids(self.admin_owner_ids_raw)

    @property
    def admin_manager_ids(self) -> tuple[int, ...]:
        return self._parse_admin_ids(self.admin_manager_ids_raw)

    @staticmethod
    def _parse_admin_ids(value: Any) -> tuple[int, ...]:
        if value is None or value == "":
            return ()

        if isinstance(value, int):
            return (value,)

        if isinstance(value, str):
            return tuple(int(item.strip()) for item in value.split(",") if item.strip())

        return tuple(int(item) for item in value)


settings = Settings()
