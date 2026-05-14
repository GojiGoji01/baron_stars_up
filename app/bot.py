from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from app.handlers import setup_routers
from app.middlewares.logging import LoggingMiddleware
from app.storage import create_fsm_storage
from config import settings


def create_bot() -> Bot:
    return Bot(
        token=settings.bot_token,
        parse_mode=ParseMode.HTML,
    )


def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher(storage=create_fsm_storage())
    dispatcher.message.middleware(LoggingMiddleware())
    dispatcher.callback_query.middleware(LoggingMiddleware())
    dispatcher.include_router(setup_routers())
    return dispatcher
