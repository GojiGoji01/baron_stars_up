import asyncio
import logging

from aiogram.exceptions import TelegramNetworkError

from app.bot import create_bot, create_dispatcher
from app.logging import setup_logging
from app.services.browser import BrowserManagerError, get_browser_manager
from app.webhooks import run_webhook_server
from config import settings


setup_logging()

logger = logging.getLogger(__name__)


async def main() -> None:
    browser_manager = get_browser_manager()
    try:
        await browser_manager.start()
    except BrowserManagerError:
        logger.exception("Playwright initialization failed")
        raise

    try:
        if settings.bot_mode == "webhook":
            bot = create_bot()
            dispatcher = create_dispatcher()
            logger.info("Bot started in webhook mode")
            try:
                await run_webhook_server(bot, dispatcher)
            finally:
                await bot.session.close()
                logger.info("Bot stopped")
            return

        while True:
            bot = create_bot()
            dispatcher = create_dispatcher()

            logger.info("Bot started in polling mode")

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
    finally:
        await browser_manager.stop()


if __name__ == "__main__":
    asyncio.run(main())
