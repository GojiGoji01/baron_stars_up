import asyncio
import logging

from aiogram.exceptions import TelegramNetworkError

from app.bot import create_bot, create_dispatcher
from app.logging import setup_logging
from config import settings


setup_logging()

logger = logging.getLogger(__name__)


async def main() -> None:
    while True:
        bot = create_bot()
        dispatcher = create_dispatcher()

        logger.info("Bot started")

        try:
            await dispatcher.start_polling(bot)
            break
        except TelegramNetworkError:
            logger.exception(
                "Telegram network error. Restarting polling in %s seconds",
                settings.polling_retry_delay,
            )
            await asyncio.sleep(settings.polling_retry_delay)
        finally:
            await bot.session.close()
            logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
