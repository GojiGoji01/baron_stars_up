import logging

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery


logger = logging.getLogger(__name__)

_EXPIRED_CALLBACK_ERRORS = (
    "query is too old",
    "query id is invalid",
    "response timeout expired",
)


async def safe_answer_callback(
    callback: CallbackQuery,
    text: str | None = None,
    *,
    show_alert: bool = False,
) -> bool:
    try:
        await callback.answer(text=text, show_alert=show_alert)
        return True
    except TelegramBadRequest as error:
        message = str(error).lower()
        if any(part in message for part in _EXPIRED_CALLBACK_ERRORS):
            logger.info(
                "callback_answer_skipped callback_id=%s reason=expired_or_invalid",
                callback.id,
            )
            return False
        raise
