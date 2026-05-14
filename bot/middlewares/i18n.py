from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Update, User
from bot.locales import get_text

class I18nMiddleware(BaseMiddleware):
    """Middleware для определения языка пользователя"""

    def __init__(self, default_language: str = "ru"):
        self.default_language = default_language
        self.user_languages: Dict[int, str] = {}

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        user: User = data.get("event_from_user")

        if user:
            # Получить или установить язык пользователя
            language = self.user_languages.get(user.id, self.default_language)
            data["language"] = language

            # Функция для быстрого получения текста
            data["i18n"] = lambda key, default="": get_text(language, key, default)

        return await handler(event, data)

    def set_user_language(self, user_id: int, language: str):
        """Установить язык для пользователя"""
        self.user_languages[user_id] = language
