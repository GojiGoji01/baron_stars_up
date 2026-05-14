from aiogram.types import InlineKeyboardButton

from bot.locales import get_text


def back_button_row(language: str) -> list[InlineKeyboardButton]:
    """Одна строка: возврат в главное меню (callback `nav_main`)."""
    return [
        InlineKeyboardButton(
            text=get_text(language, "btn_back"),
            callback_data="nav_main",
        )
    ]
