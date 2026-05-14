import asyncio
import logging

from app.bot import create_bot, create_dispatcher
from config import settings


logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def main() -> None:
    bot = create_bot()
    dispatcher = create_dispatcher()

    logger.info("Bot started")

    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
