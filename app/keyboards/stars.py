from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.keyboards.common import add_button, get_back_button
from app.utils.callbacks import BuyCallbacks, MenuCallbacks, StarsCallbacks


def build_stars_recipient_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(text="СЕБЕ", callback_data=StarsCallbacks.SELF)
    builder.button(text="ДРУГУ", callback_data=StarsCallbacks.FRIEND)
    add_button(builder, get_back_button(MenuCallbacks.MAIN))
    builder.adjust(2, 1)

    return builder.as_markup()


def get_stars_amount_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for amount in (50, 100, 250, 500):
        builder.button(text=f"{amount} ⭐️", callback_data=StarsCallbacks.amount(amount))

    builder.button(text="✏️ Другая сумма", callback_data=StarsCallbacks.AMOUNT_CUSTOM)
    builder.button(text="👤 Выбрать получателя", callback_data=StarsCallbacks.FRIEND)
    add_button(builder, get_back_button(BuyCallbacks.STARS))
    builder.adjust(2, 2, 1, 1, 1)

    return builder.as_markup()


def build_stars_amount_keyboard() -> InlineKeyboardMarkup:
    return get_stars_amount_keyboard()
