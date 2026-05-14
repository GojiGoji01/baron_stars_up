from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.keyboards.common import add_button, get_main_menu_button
from app.utils.callbacks import TonCallbacks


def build_ton_amount_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for amount in (1, 5, 10, 25):
        builder.button(text=f"{amount} TON", callback_data=TonCallbacks.amount(amount))

    builder.button(text="✏️ Другая сумма", callback_data=TonCallbacks.AMOUNT_CUSTOM)
    add_button(builder, get_main_menu_button())
    builder.adjust(2, 2, 1, 1)

    return builder.as_markup()
