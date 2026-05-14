from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu_keyboard(language: str) -> InlineKeyboardMarkup:
    """Главное меню"""
    from bot.locales import get_text

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=get_text(language, "btn_buy"),
                callback_data="buy"
            )],
            [InlineKeyboardButton(
                text=get_text(language, "btn_partners"),
                callback_data="partners"
            )],
            [InlineKeyboardButton(
                text=get_text(language, "btn_help"),
                callback_data="help"
            )],
            [InlineKeyboardButton(
                text=get_text(language, "btn_news"),
                callback_data="news"
            )],
            [InlineKeyboardButton(
                text=get_text(language, "btn_language"),
                callback_data="set_language"
            )],
        ]
    )
    return keyboard

def get_language_keyboard() -> InlineKeyboardMarkup:
    """Выбор языка"""
    from bot.locales import get_text

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text("ru", "btn_ru"),
                    callback_data="lang_ru"
                ),
                InlineKeyboardButton(
                    text=get_text("en", "btn_en"),
                    callback_data="lang_en"
                ),
            ],
        ]
    )
    return keyboard
