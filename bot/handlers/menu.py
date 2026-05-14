from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from bot.keyboards import back_button_row, get_main_menu_keyboard
from bot.locales import get_text
from bot.states import MenuStates
from config import config

router = Router(name="menu")


def _help_keyboard(language: str) -> InlineKeyboardMarkup:
    manager_url = f"https://t.me/{config.MANAGER_USERNAME.lstrip('@')}"
    rows = [
        [
            InlineKeyboardButton(
                text=get_text(language, "btn_open_manager"),
                url=manager_url,
            )
        ],
        back_button_row(language),
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _news_keyboard(language: str) -> InlineKeyboardMarkup:
    channel = config.NEWS_CHANNEL_USERNAME.lstrip("@")
    channel_url = f"https://t.me/{channel}"
    rows = [
        [
            InlineKeyboardButton(
                text=get_text(language, "btn_open_channel"),
                url=channel_url,
            )
        ],
        back_button_row(language),
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _simple_back_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[back_button_row(language)])


@router.callback_query(F.data == "partners", MenuStates.main_menu)
async def open_partners(query: CallbackQuery, state: FSMContext, language: str, i18n):
    await state.set_state(MenuStates.partners_hub)
    await query.message.edit_text(
        i18n("screen_partners"),
        reply_markup=_simple_back_keyboard(language),
    )
    await query.answer()


@router.callback_query(F.data == "help", MenuStates.main_menu)
async def open_help(query: CallbackQuery, state: FSMContext, language: str, i18n):
    await state.set_state(MenuStates.help_screen)
    await query.message.edit_text(
        i18n("screen_help"),
        reply_markup=_help_keyboard(language),
    )
    await query.answer()


@router.callback_query(F.data == "news", MenuStates.main_menu)
async def open_news(query: CallbackQuery, state: FSMContext, language: str, i18n):
    await state.set_state(MenuStates.news_screen)
    await query.message.edit_text(
        i18n("screen_news"),
        reply_markup=_news_keyboard(language),
    )
    await query.answer()


@router.callback_query(F.data == "nav_main")
async def back_to_main(query: CallbackQuery, state: FSMContext, language: str, i18n):
    """Назад: главное меню (доступно с экранов разделов)."""
    await state.clear()
    await state.set_state(MenuStates.main_menu)
    await query.message.edit_text(
        i18n("start_text"),
        reply_markup=get_main_menu_keyboard(language),
    )
    await query.answer()
