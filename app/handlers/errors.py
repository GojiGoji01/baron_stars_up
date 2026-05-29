import logging

from aiogram import Router
from aiogram.types import ErrorEvent

from app.utils.telegram import safe_answer_callback


router = Router(name="errors")
logger = logging.getLogger(__name__)


@router.errors()
async def handle_error(event: ErrorEvent) -> bool:
    logger.error(
        "Unhandled update error update=%s",
        event.update,
        exc_info=(
            type(event.exception),
            event.exception,
            event.exception.__traceback__,
        ),
    )

    if event.update.callback_query:
        await safe_answer_callback(
            event.update.callback_query,
            "Произошла ошибка. Попробуйте еще раз.",
            show_alert=True,
        )
        return True

    if event.update.message:
        await event.update.message.answer("Произошла ошибка. Попробуйте еще раз.")
        return True

    return True
