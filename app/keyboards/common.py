from dataclasses import dataclass

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils.callbacks import MenuCallbacks, PaymentCallbacks, StarsCallbacks


@dataclass(frozen=True)
class KeyboardButtonSpec:
    text: str
    callback_data: str


def get_back_button(callback_data: str) -> KeyboardButtonSpec:
    return KeyboardButtonSpec(text="↩️ Назад", callback_data=callback_data)


def get_main_menu_button() -> KeyboardButtonSpec:
    return get_back_button(MenuCallbacks.MAIN)


def get_cancel_button(callback_data: str = MenuCallbacks.MAIN) -> KeyboardButtonSpec:
    return KeyboardButtonSpec(text="Отмена", callback_data=callback_data)


def add_button(builder: InlineKeyboardBuilder, button: KeyboardButtonSpec) -> None:
    builder.button(text=button.text, callback_data=button.callback_data)


def build_single_button_keyboard(button: KeyboardButtonSpec) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    add_button(builder, button)
    builder.adjust(1)

    return builder.as_markup()


def build_custom_amount_keyboard(
    back_callback_data: str = StarsCallbacks.AMOUNT_BACK,
) -> InlineKeyboardMarkup:
    return build_single_button_keyboard(get_back_button(back_callback_data))


def build_payment_method_keyboard(back_callback_data: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(text="💎 TON", callback_data=PaymentCallbacks.TON)
    add_button(builder, get_back_button(back_callback_data))
    builder.adjust(1)

    return builder.as_markup()
