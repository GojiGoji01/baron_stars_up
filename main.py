import asyncio
import logging

from app.bot import create_bot, create_dispatcher
from app.logging import setup_logging


setup_logging()

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
