import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject


logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user_id = None
        action = event.__class__.__name__

        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
            action = f"message:{event.text or event.content_type}"
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            action = f"callback:{event.data}"

        state = data.get("state")
        state_name = await state.get_state() if state else None

        logger.info(
            "user_action user_id=%s action=%s state=%s",
            user_id,
            action,
            state_name,
        )

        return await handler(event, data)
