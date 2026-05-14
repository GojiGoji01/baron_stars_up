from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage
from bot.middlewares import I18nMiddleware
from bot.handlers import router
from config import config

async def setup_dispatcher(bot: Bot) -> Dispatcher:
    """Инициализация диспетчера"""
    dp = Dispatcher(storage=MemoryStorage())

    # Установка middleware
    i18n = I18nMiddleware(default_language=config.DEFAULT_LANGUAGE)
    dp["i18n_middleware"] = i18n
    dp.message.middleware(i18n)
    dp.callback_query.middleware(i18n)

    # Регистрация роутеров
    dp.include_router(router)

    return dp
