from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.keyboards.common import add_button, get_main_menu_button
from app.utils.callbacks import ProfileCallbacks


def build_profile_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(text="Connect Tonkeeper", callback_data=ProfileCallbacks.CONNECT_WALLET)
    builder.button(text="Verify Wallet", callback_data=ProfileCallbacks.VERIFY_WALLET)
    builder.button(text="Disconnect Wallet", callback_data=ProfileCallbacks.DISCONNECT_WALLET)
    builder.button(text="Р’С‹РІРµСЃС‚Рё Р·РІРµР·РґС‹", callback_data=ProfileCallbacks.WITHDRAW_STARS)
    add_button(builder, get_main_menu_button())
    builder.adjust(1, 1, 1, 1, 1)

    return builder.as_markup()
