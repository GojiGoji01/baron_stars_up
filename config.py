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
        default="app/assets/welcomebaron.png",
        alias="START_IMAGE_URL",
    )
    support_manager_url: str = Field(default="https://t.me/support", alias="SUPPORT_MANAGER_URL")
    manager_username: str = Field(default="", alias="MANAGER_USERNAME")

    bot_mode: str = Field(default="polling", alias="BOT_MODE")
    webhook_base_url: str = Field(default="", alias="WEBHOOK_BASE_URL")
    webhook_host: str = Field(default="0.0.0.0", alias="WEBHOOK_HOST")
    webhook_port: int = Field(default=8000, alias="WEBHOOK_PORT")

    telegram_webhook_path: str = Field(default="/webhooks/telegram", alias="TELEGRAM_WEBHOOK_PATH")
    telegram_webhook_secret: str = Field(default="", alias="TELEGRAM_WEBHOOK_SECRET")
    telegram_delete_webhook_on_shutdown: bool = Field(
        default=False,
        alias="TELEGRAM_DELETE_WEBHOOK_ON_SHUTDOWN",
    )

    platega_webhook_path: str = Field(default="/webhooks/platega", alias="PLATEGA_WEBHOOK_PATH")
    cryptobot_webhook_path: str = Field(default="/webhooks/cryptobot", alias="CRYPTOBOT_WEBHOOK_PATH")

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
    cryptobot_api_base_url: str = Field(default="https://pay.crypt.bot/api", alias="CRYPTOBOT_API_BASE_URL")
    cryptobot_asset: str = Field(default="USDT", alias="CRYPTOBOT_ASSET")
    cryptobot_invoice_expires_seconds: int = Field(default=900, alias="CRYPTOBOT_INVOICE_EXPIRES_SECONDS")

    referrals_enabled: bool = Field(default=False, alias="REFERRALS_ENABLED")
    referral_percent: int = Field(default=70, alias="REFERRAL_PERCENT")
    referral_base: str = Field(default="profit", alias="REFERRAL_BASE")

    min_stars_amount: int = Field(default=50, alias="MIN_STARS_AMOUNT")
    max_stars_amount: int = Field(default=50000, alias="MAX_STARS_AMOUNT")
    order_timeout_minutes: int = Field(default=15, alias="ORDER_TIMEOUT_MINUTES")
    service_commission_percent: float = Field(default=3.0, alias="SERVICE_COMMISSION_PERCENT")
    default_usd_rub_rate: float = Field(default=100.0, alias="DEFAULT_USD_RUB_RATE")
    exchange_rate_provider: str = Field(default="bybit", alias="EXCHANGE_RATE_PROVIDER")
    exchange_rate_cache_seconds: int = Field(default=60, alias="EXCHANGE_RATE_CACHE_SECONDS")
    exchange_rate_spread_percent: float = Field(default=3.0, alias="EXCHANGE_RATE_SPREAD_PERCENT")
    bybit_p2p_amount: str = Field(default="10000", alias="BYBIT_P2P_AMOUNT")
    price_rates_cache_ttl_seconds: int = Field(default=300, alias="PRICE_RATES_CACHE_TTL_SECONDS")
    price_fallback_to_static_rate: bool = Field(default=True, alias="PRICE_FALLBACK_TO_STATIC_RATE")

    http_timeout: float = Field(default=15.0, alias="HTTP_TIMEOUT")
    http_retry_attempts: int = Field(default=3, alias="HTTP_RETRY_ATTEMPTS")
    http_retry_delay: float = Field(default=0.5, alias="HTTP_RETRY_DELAY")

    polling_retry_delay: float = Field(default=10.0, alias="POLLING_RETRY_DELAY")
    playwright_enabled: bool = Field(default=True, alias="PLAYWRIGHT_ENABLED")
    playwright_headless: bool = Field(default=True, alias="PLAYWRIGHT_HEADLESS")
    playwright_no_sandbox: bool = Field(default=True, alias="PLAYWRIGHT_NO_SANDBOX")
    playwright_userdata_dir: str = Field(default="./userdata", alias="PLAYWRIGHT_USERDATA_DIR")
    playwright_launch_timeout_ms: int = Field(default=30000, alias="PLAYWRIGHT_LAUNCH_TIMEOUT_MS")

    platega_api_base_url: str = Field(default="https://app.platega.io", alias="PLATEGA_API_BASE_URL")
    platega_merchant_id: str = Field(default="", alias="PLATEGA_MERCHANT_ID")
    platega_secret: str = Field(default="", alias="PLATEGA_SECRET")
    platega_success_url: str = Field(default="", alias="PLATEGA_SUCCESS_URL")
    platega_failed_url: str = Field(default="", alias="PLATEGA_FAILED_URL")
    platega_timeout_seconds: float = Field(default=20.0, alias="PLATEGA_TIMEOUT_SECONDS")
    platega_commission_percent: float = Field(default=0.0, alias="PLATEGA_COMMISSION_PERCENT")
    platega_display_commission_percent: float = Field(default=8.0, alias="PLATEGA_DISPLAY_COMMISSION_PERCENT")

    fragment_api_base_url: str = Field(default="", alias="FRAGMENT_API_BASE_URL")
    fragment_api_url: str = Field(default="", alias="FRAGMENT_API_URL")
    fragment_api_key: str = Field(default="", alias="FRAGMENT_API_KEY")
    fragment_wallet_mnemonic: str = Field(default="", alias="FRAGMENT_WALLET_MNEMONIC")
    fragment_api_mode: str = Field(default="kyc", alias="FRAGMENT_API_MODE")
    fragment_cookies_base64: str = Field(default="", alias="FRAGMENT_COOKIES_BASE64")
    fragment_local_storage_base64: str = Field(default="", alias="FRAGMENT_LOCAL_STORAGE_BASE64")
    fragment_web_base_url: str = Field(default="https://fragment.com", alias="FRAGMENT_WEB_BASE_URL")
    fragment_browser_timeout_ms: int = Field(default=20000, alias="FRAGMENT_BROWSER_TIMEOUT_MS")
    fragment_browser_screenshots_dir: str = Field(
        default="./logs/fragment",
        alias="FRAGMENT_BROWSER_SCREENSHOTS_DIR",
    )
    fragment_browser_prefer_userdata_profile: bool = Field(
        default=False,
        alias="FRAGMENT_BROWSER_PREFER_USERDATA_PROFILE",
    )
    fragment_star_base_usd: float = Field(default=0.015, alias="FRAGMENT_STAR_BASE_USD")
    fragment_timeout_seconds: float = Field(default=20.0, alias="FRAGMENT_TIMEOUT_SECONDS")
    fragment_max_delivery_attempts: int = Field(default=3, alias="FRAGMENT_MAX_DELIVERY_ATTEMPTS")
    telegram_api_base_url: str = Field(default="https://api.telegram.org", alias="TELEGRAM_API_BASE_URL")
    telegram_gifts_cache_seconds: int = Field(default=300, alias="TELEGRAM_GIFTS_CACHE_SECONDS")
    premium_price_3_months: float = Field(default=999.0, alias="PREMIUM_PRICE_3_MONTHS")
    premium_price_6_months: float = Field(default=1699.0, alias="PREMIUM_PRICE_6_MONTHS")
    premium_price_12_months: float = Field(default=2999.0, alias="PREMIUM_PRICE_12_MONTHS")

    @field_validator("fsm_storage", mode="before")
    @classmethod
    def normalize_fsm_storage(cls, value: Any) -> str:
        return str(value or "memory").lower()

    @field_validator("bot_mode", mode="before")
    @classmethod
    def normalize_bot_mode(cls, value: Any) -> str:
        mode = str(value or "polling").lower()
        return mode if mode in {"polling", "webhook"} else "polling"

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: Any) -> str:
        return str(value or "INFO").upper()

    @field_validator("exchange_rate_provider", mode="before")
    @classmethod
    def normalize_exchange_rate_provider(cls, value: Any) -> str:
        provider = str(value or "bybit").lower()
        if provider in {"bybit", "bybit_p2p"}:
            return provider
        return "bybit"

    @field_validator("fragment_api_mode", mode="before")
    @classmethod
    def normalize_fragment_api_mode(cls, value: Any) -> str:
        mode = str(value or "kyc").lower()
        return mode if mode in {"kyc", "no_kyc"} else "kyc"

    @property
    def fragment_effective_api_url(self) -> str:
        return self.fragment_api_base_url or self.fragment_api_url

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
