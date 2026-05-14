from dataclasses import dataclass
from os import getenv

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_id: int
    start_image_url: str
    support_manager_url: str
    fsm_storage: str
    redis_url: str
    log_level: str
    database_url: str
    admin_owner_ids: tuple[int, ...]
    admin_manager_ids: tuple[int, ...]
    cryptobot_api_token: str
    cryptobot_webhook_secret: str
    referrals_enabled: bool
    referral_percent: int
    referral_base: str


def _parse_int_tuple(value: str | None) -> tuple[int, ...]:
    if not value:
        return ()

    return tuple(int(item.strip()) for item in value.split(",") if item.strip())


def _parse_bool(value: str | None) -> bool:
    return str(value).lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    bot_token = getenv("BOT_TOKEN")

    if not bot_token:
        raise ValueError("BOT_TOKEN is not set")

    return Settings(
        bot_token=bot_token,
        admin_id=int(getenv("ADMIN_ID", "0")),
        start_image_url=getenv(
            "START_IMAGE_URL",
            "https://placehold.co/1024x512/png?text=Telegram+Stars+Premium",
        ),
        support_manager_url=getenv("SUPPORT_MANAGER_URL", "https://t.me/support"),
        fsm_storage=getenv("FSM_STORAGE", "memory").lower(),
        redis_url=getenv("REDIS_URL", "redis://localhost:6379/0"),
        log_level=getenv("LOG_LEVEL", "INFO").upper(),
        database_url=getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://tg_star:tg_star_password@localhost:5432/tg_star",
        ),
        admin_owner_ids=_parse_int_tuple(getenv("ADMIN_OWNER_IDS")),
        admin_manager_ids=_parse_int_tuple(getenv("ADMIN_MANAGER_IDS")),
        cryptobot_api_token=getenv("CRYPTOBOT_API_TOKEN", ""),
        cryptobot_webhook_secret=getenv("CRYPTOBOT_WEBHOOK_SECRET", ""),
        referrals_enabled=_parse_bool(getenv("REFERRALS_ENABLED", "false")),
        referral_percent=int(getenv("REFERRAL_PERCENT", "70")),
        referral_base=getenv("REFERRAL_BASE", "profit"),
    )


settings = load_settings()
