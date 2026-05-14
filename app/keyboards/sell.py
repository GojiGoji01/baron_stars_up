from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.keyboards.common import add_button, get_main_menu_button
from app.utils.callbacks import SellCallbacks


def build_sell_stars_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(text="50 ⭐️", callback_data=SellCallbacks.amount(50))
    builder.button(text="100 ⭐️", callback_data=SellCallbacks.amount(100))
    builder.button(text="1000 ⭐️", callback_data=SellCallbacks.amount(1000))
    builder.button(text="✏️ Ввести количество", callback_data=SellCallbacks.AMOUNT_CUSTOM)
    add_button(builder, get_main_menu_button())
    builder.adjust(3, 1, 1)

    return builder.as_markup()
