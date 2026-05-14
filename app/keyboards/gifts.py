from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.keyboards.common import add_button, get_back_button
from app.services.gifts import AVAILABLE_GIFTS
from app.utils.callbacks import BuyCallbacks, GiftCallbacks, MenuCallbacks


def build_gift_recipient_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(text="СЕБЕ", callback_data=GiftCallbacks.SELF)
    builder.button(text="ДРУГУ", callback_data=GiftCallbacks.FRIEND)
    add_button(builder, get_back_button(MenuCallbacks.MAIN))
    builder.adjust(2, 1)

    return builder.as_markup()


def build_gift_list_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for gift in AVAILABLE_GIFTS:
        builder.button(
            text=f"{gift['title']} — {gift['price']} ₽",
            callback_data=GiftCallbacks.select(gift["gift_id"]),
        )

    builder.button(text="👤 Выбрать получателя", callback_data=GiftCallbacks.FRIEND)
    add_button(builder, get_back_button(BuyCallbacks.GIFT))
    builder.adjust(1)

    return builder.as_markup()
