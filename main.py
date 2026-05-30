import asyncio
import logging

from aiogram.exceptions import TelegramNetworkError

from app.bot import create_bot, create_dispatcher
from app.logging import setup_logging
from app.services.browser import BrowserManagerError, get_browser_manager
from app.services.lifecycle import run_service_until_shutdown
from app.webhooks import run_webhook_server
from config import settings


setup_logging()

logger = logging.getLogger(__name__)


async def run_bot_service() -> None:
    browser_manager = get_browser_manager()
    try:
        await browser_manager.start()
    except BrowserManagerError:
        logger.exception("Playwright initialization failed")
        raise

    if settings.bot_mode == "webhook":
        bot = create_bot()
        dispatcher = create_dispatcher()
        logger.info("Bot started in webhook mode")
        try:
            await run_webhook_server(bot, dispatcher)
        except asyncio.CancelledError:
            logger.info("Webhook mode shutdown requested")
            raise
        finally:
            await bot.session.close()
            logger.info("Bot stopped")
        return

    while True:
        bot = create_bot()
        dispatcher = create_dispatcher()

        logger.info("Bot started in polling mode")

        try:
            await dispatcher.start_polling(bot, handle_signals=False)
            break
        except TelegramNetworkError:
            logger.exception(
                "Telegram network error. Restarting polling in %s seconds",
                settings.polling_retry_delay,
            )
            await asyncio.sleep(settings.polling_retry_delay)
        except asyncio.CancelledError:
            logger.info("Polling mode shutdown requested")
            raise
        finally:
            await bot.session.close()
            logger.info("Bot stopped")


async def main() -> None:
    # systemd-friendly shutdown is handled via SIGINT/SIGTERM so Playwright can
    # close pages, context and driver before the process exits.
    await run_service_until_shutdown(run_bot_service)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("service_stopped_by_signal")
