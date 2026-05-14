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
    )


settings = load_settings()
