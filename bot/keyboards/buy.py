from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.keyboards.nav import back_button_row
from bot.locales import get_text

STARS_PRESETS = (50, 100, 250, 500)
PREMIUM_MONTHS = (1, 3, 6, 12)


def choose_product_keyboard(language: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=get_text(language, "btn_buy_stars"),
                callback_data="b_prod_s",
            ),
            InlineKeyboardButton(
                text=get_text(language, "btn_buy_premium"),
                callback_data="b_prod_p",
            ),
        ],
        back_button_row(language),
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def stars_recipient_keyboard(language: str) -> InlineKeyboardMarkup:
    """Назад к выбору количества звёзд."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text(language, "btn_back"),
                    callback_data="b_nav_sr",
                )
            ]
        ]
    )


def stars_amount_keyboard(language: str) -> InlineKeyboardMarkup:
    row_buttons = [
        InlineKeyboardButton(text=str(n), callback_data=f"b_st_{n}")
        for n in STARS_PRESETS
    ]
    rows = [row_buttons[i : i + 2] for i in range(0, len(row_buttons), 2)]
    rows.append(
        [
            InlineKeyboardButton(
                text=get_text(language, "btn_stars_custom"),
                callback_data="b_st_c",
            )
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                text=get_text(language, "btn_back"),
                callback_data="b_nav_pt",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def stars_custom_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text(language, "btn_back"),
                    callback_data="b_nav_sa",
                )
            ]
        ]
    )


def premium_duration_keyboard(language: str) -> InlineKeyboardMarkup:
    rows = []
    row: list[InlineKeyboardButton] = []
    for m in PREMIUM_MONTHS:
        row.append(
            InlineKeyboardButton(
                text=get_text(language, f"btn_premium_{m}m"),
                callback_data=f"b_pr_{m}",
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append(
        [
            InlineKeyboardButton(
                text=get_text(language, "btn_back"),
                callback_data="b_nav_pt",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def premium_recipient_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text(language, "btn_back"),
                    callback_data="b_nav_pd",
                )
            ]
        ]
    )


def payment_placeholder_keyboard(language: str, product: str) -> InlineKeyboardMarkup:
    """product: 'stars' | 'premium' — куда вернуться для правки."""
    back_cb = "b_ps_st" if product == "stars" else "b_ps_pr"
    rows = [
        [
            InlineKeyboardButton(
                text=get_text(language, "btn_edit_step"),
                callback_data=back_cb,
            )
        ],
        back_button_row(language),
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
