from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.keyboards.common import add_button, get_back_button
from app.utils.callbacks import BuyCallbacks, MenuCallbacks, PaymentCallbacks, PremiumCallbacks


def get_premium_duration_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(text="3 месяца", callback_data=PremiumCallbacks.duration(3))
    builder.button(text="6 месяцев", callback_data=PremiumCallbacks.duration(6))
    builder.button(text="12 месяцев", callback_data=PremiumCallbacks.duration(12))
    add_button(builder, get_back_button(MenuCallbacks.MAIN))
    builder.adjust(1)

    return builder.as_markup()


def build_premium_duration_keyboard() -> InlineKeyboardMarkup:
    return get_premium_duration_keyboard()


def build_premium_target_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(text="СЕБЕ", callback_data=PremiumCallbacks.SELF)
    builder.button(text="ДРУГУ", callback_data=PremiumCallbacks.FRIEND)
    add_button(builder, get_back_button(BuyCallbacks.PREMIUM))
    builder.adjust(2, 1)

    return builder.as_markup()


def build_premium_recipient_keyboard(
    show_recipient_button: bool = True,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if show_recipient_button:
        builder.button(text="👤 Выбрать получателя", callback_data=PremiumCallbacks.FRIEND)

    builder.button(text="Продолжить", callback_data=PaymentCallbacks.TON)
    add_button(builder, get_back_button(BuyCallbacks.PREMIUM))
    builder.adjust(1)

    return builder.as_markup()
