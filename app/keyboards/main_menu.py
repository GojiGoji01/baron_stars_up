from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.keyboards.common import add_button, build_single_button_keyboard, get_main_menu_button
from app.utils.callbacks import (
    BuyCallbacks,
    MenuCallbacks,
    ProfileCallbacks,
    ReferralCallbacks,
)
from config import settings


def _get_support_manager_url() -> str:
    username = settings.manager_username.lstrip("@")
    if username:
        return f"https://t.me/{username}"
    return settings.support_manager_url


def build_main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(text="⭐️ Купить звезды", callback_data=BuyCallbacks.STARS)
    builder.button(text="⚜️ Premium", callback_data=BuyCallbacks.PREMIUM)
    builder.button(text="🎁 Купить подарок", callback_data=BuyCallbacks.GIFT)
    builder.button(text="🤝 Реферальная система", callback_data=ReferralCallbacks.OPEN)
    builder.button(text="🛟 Поддержка", callback_data=MenuCallbacks.SUPPORT)
    builder.button(text="ℹ️ Информация", callback_data=MenuCallbacks.INFO)
    builder.button(text="👤 Профиль", callback_data=ProfileCallbacks.OPEN)
    builder.adjust(2, 1, 2, 1)

    return builder.as_markup()


def build_buy_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(text="⭐️ STARS", callback_data=BuyCallbacks.STARS)
    builder.button(text="⚜️ PREMIUM", callback_data=BuyCallbacks.PREMIUM)
    builder.button(text="↩️ Назад", callback_data=MenuCallbacks.MAIN)
    builder.adjust(1)

    return builder.as_markup()


def build_back_to_main_keyboard() -> InlineKeyboardMarkup:
    return build_single_button_keyboard(get_main_menu_button())


def build_back_to_buy_keyboard() -> InlineKeyboardMarkup:
    return build_single_button_keyboard(get_main_menu_button())


def build_support_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(text="🛟 Написать менеджеру", url=_get_support_manager_url())
    add_button(builder, get_main_menu_button())
    builder.adjust(1)

    return builder.as_markup()


def build_info_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(
        text="📄 Правила",
        url="https://telegra.ph/Polzovatelskoe-soglashenie-04-01-19",
    )
    builder.button(
        text="🔒 Конфиденциальность",
        url="https://telegra.ph/Politika-konfidencialnosti-04-01-26",
    )
    builder.button(text="Поддержка", url=_get_support_manager_url())
    add_button(builder, get_main_menu_button())
    builder.adjust(2, 1, 1)

    return builder.as_markup()
