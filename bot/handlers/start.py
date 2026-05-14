from aiogram import Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from bot.middlewares.i18n import I18nMiddleware
from bot.states import MenuStates
from bot.keyboards import get_language_keyboard, get_main_menu_keyboard
from bot.locales import get_text

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, language: str, i18n):
    """Обработка команды /start"""
    await state.clear()
    await state.set_state(MenuStates.main_menu)

    text = i18n("start_text")
    keyboard = get_main_menu_keyboard(language)

    await message.answer(text, reply_markup=keyboard)

@router.callback_query(F.data == "set_language", MenuStates.main_menu)
async def set_language_menu(query: CallbackQuery, state: FSMContext, language: str, i18n):
    """Показать меню выбора языка"""
    await state.set_state(MenuStates.language_select)

    text = i18n("language_select")
    keyboard = get_language_keyboard()

    await query.message.edit_text(text, reply_markup=keyboard)
    await query.answer()

@router.callback_query(F.data == "lang_ru")
async def set_lang_ru(query: CallbackQuery, state: FSMContext, dispatcher: Dispatcher):
    """Установить русский язык"""
    i18n_mw: I18nMiddleware = dispatcher["i18n_middleware"]
    i18n_mw.set_user_language(query.from_user.id, "ru")

    await state.clear()
    await state.set_state(MenuStates.main_menu)

    text = get_text("ru", "start_text")
    keyboard = get_main_menu_keyboard("ru")

    await query.message.edit_text(text, reply_markup=keyboard)
    await query.answer("🇷🇺 Язык изменён на русский")

@router.callback_query(F.data == "lang_en")
async def set_lang_en(query: CallbackQuery, state: FSMContext, dispatcher: Dispatcher):
    """Установить английский язык"""
    i18n_mw: I18nMiddleware = dispatcher["i18n_middleware"]
    i18n_mw.set_user_language(query.from_user.id, "en")

    await state.clear()
    await state.set_state(MenuStates.main_menu)

    text = get_text("en", "start_text")
    keyboard = get_main_menu_keyboard("en")

    await query.message.edit_text(text, reply_markup=keyboard)
    await query.answer("🇬🇧 Language changed to English")
