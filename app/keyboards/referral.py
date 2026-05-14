from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.keyboards.common import add_button, get_main_menu_button
from app.utils.callbacks import ReferralCallbacks


def build_referrals_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(text="Вывести", callback_data=ReferralCallbacks.WITHDRAW)
    builder.button(text="Мои рефералы", callback_data=ReferralCallbacks.LIST)
    add_button(builder, get_main_menu_button())
    builder.adjust(2, 1)

    return builder.as_markup()
