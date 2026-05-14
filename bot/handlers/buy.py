from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from bot.keyboards import (
    choose_product_keyboard,
    payment_placeholder_keyboard,
    premium_duration_keyboard,
    premium_recipient_keyboard,
    stars_amount_keyboard,
    stars_custom_keyboard,
    stars_recipient_keyboard,
)
from bot.locales import get_text
from bot.services.validators import normalize_username, parse_stars_amount
from bot.states import BuyStates, MenuStates

router = Router(name="buy")


@router.callback_query(F.data == "buy", MenuStates.main_menu)
async def open_buy(query: CallbackQuery, state: FSMContext, language: str, i18n):
    await state.clear()
    await state.set_state(BuyStates.choose_type)
    await query.message.edit_text(
        i18n("buy_choose_product"),
        reply_markup=choose_product_keyboard(language),
    )
    await query.answer()


@router.callback_query(BuyStates.choose_type, F.data == "b_prod_s")
async def choose_stars(query: CallbackQuery, state: FSMContext, language: str, i18n):
    await state.update_data(product="stars")
    await state.set_state(BuyStates.stars_amount)
    await query.message.edit_text(
        i18n("stars_ask_amount"),
        reply_markup=stars_amount_keyboard(language),
    )
    await query.answer()


@router.callback_query(BuyStates.choose_type, F.data == "b_prod_p")
async def choose_premium(query: CallbackQuery, state: FSMContext, language: str, i18n):
    await state.update_data(product="premium")
    await state.set_state(BuyStates.premium_duration)
    await query.message.edit_text(
        i18n("premium_ask_duration"),
        reply_markup=premium_duration_keyboard(language),
    )
    await query.answer()


@router.callback_query(
    StateFilter(BuyStates.stars_amount, BuyStates.premium_duration),
    F.data == "b_nav_pt",
)
async def back_to_choose_type(query: CallbackQuery, state: FSMContext, language: str, i18n):
    await state.clear()
    await state.set_state(BuyStates.choose_type)
    await query.message.edit_text(
        i18n("buy_choose_product"),
        reply_markup=choose_product_keyboard(language),
    )
    await query.answer()


@router.callback_query(BuyStates.stars_recipient, F.data == "b_nav_sr")
async def stars_recipient_back_amount(query: CallbackQuery, state: FSMContext, language: str, i18n):
    await state.update_data(stars_recipient=None)
    await state.set_state(BuyStates.stars_amount)
    await query.message.edit_text(
        i18n("stars_ask_amount"),
        reply_markup=stars_amount_keyboard(language),
    )
    await query.answer()


@router.message(BuyStates.stars_recipient, F.text)
async def stars_recipient_entered(message: Message, state: FSMContext, language: str, i18n):
    username = normalize_username(message.text)
    if not username:
        await message.answer(i18n("err_username"))
        return
    await state.update_data(stars_recipient=username)
    await state.set_state(BuyStates.payment_method)
    data = await state.get_data()
    text = _summary_stars(language, data)
    await message.answer(
        text,
        reply_markup=payment_placeholder_keyboard(language, "stars"),
    )


@router.callback_query(BuyStates.stars_amount, F.data == "b_st_c")
async def stars_pick_custom(query: CallbackQuery, state: FSMContext, language: str, i18n):
    await state.set_state(BuyStates.stars_custom_amount)
    await query.message.edit_text(
        i18n("stars_ask_custom"),
        reply_markup=stars_custom_keyboard(language),
    )
    await query.answer()


@router.callback_query(BuyStates.stars_custom_amount, F.data == "b_nav_sa")
async def stars_custom_back_amount(query: CallbackQuery, state: FSMContext, language: str, i18n):
    await state.set_state(BuyStates.stars_amount)
    await query.message.edit_text(
        i18n("stars_ask_amount"),
        reply_markup=stars_amount_keyboard(language),
    )
    await query.answer()


@router.message(BuyStates.stars_custom_amount, F.text)
async def stars_custom_entered(message: Message, state: FSMContext, language: str, i18n):
    amount = parse_stars_amount(message.text)
    if amount is None:
        await message.answer(i18n("err_stars_amount"))
        return
    await state.update_data(stars_amount=amount)
    await state.set_state(BuyStates.stars_recipient)
    await message.answer(
        i18n("stars_ask_recipient"),
        reply_markup=stars_recipient_keyboard(language),
    )


@router.callback_query(BuyStates.stars_amount, F.data.regexp(r"^b_st_\d+$"))
async def stars_preset_amount(query: CallbackQuery, state: FSMContext, language: str, i18n):
    try:
        amount = int(query.data.removeprefix("b_st_"))
    except ValueError:
        await query.answer()
        return
    await state.update_data(stars_amount=amount)
    await state.set_state(BuyStates.stars_recipient)
    await query.message.edit_text(
        i18n("stars_ask_recipient"),
        reply_markup=stars_recipient_keyboard(language),
    )
    await query.answer()


def _summary_stars(language: str, data: dict) -> str:
    return get_text(language, "summary_stars").format(
        recipient=data.get("stars_recipient", "—"),
        amount=data.get("stars_amount", "—"),
        next_hint=get_text(language, "payment_next_phase"),
    )


def _summary_premium(language: str, data: dict) -> str:
    months = data.get("premium_months", "—")
    return get_text(language, "summary_premium").format(
        months=months,
        recipient=data.get("premium_recipient", "—"),
        next_hint=get_text(language, "payment_next_phase"),
    )


@router.callback_query(BuyStates.premium_duration, F.data.regexp(r"^b_pr_(1|3|6|12)$"))
async def premium_duration_chosen(query: CallbackQuery, state: FSMContext, language: str, i18n):
    try:
        months = int(query.data.removeprefix("b_pr_"))
    except ValueError:
        await query.answer()
        return
    await state.update_data(premium_months=months)
    await state.set_state(BuyStates.premium_recipient)
    await query.message.edit_text(
        i18n("premium_ask_recipient"),
        reply_markup=premium_recipient_keyboard(language),
    )
    await query.answer()


@router.callback_query(BuyStates.premium_recipient, F.data == "b_nav_pd")
async def premium_recipient_back_duration(query: CallbackQuery, state: FSMContext, language: str, i18n):
    await state.update_data(premium_recipient=None)
    await state.set_state(BuyStates.premium_duration)
    await query.message.edit_text(
        i18n("premium_ask_duration"),
        reply_markup=premium_duration_keyboard(language),
    )
    await query.answer()


@router.message(BuyStates.premium_recipient, F.text)
async def premium_recipient_entered(message: Message, state: FSMContext, language: str, i18n):
    username = normalize_username(message.text)
    if not username:
        await message.answer(i18n("err_username"))
        return
    await state.update_data(premium_recipient=username)
    await state.set_state(BuyStates.payment_method)
    data = await state.get_data()
    text = _summary_premium(language, data)
    await message.answer(
        text,
        reply_markup=payment_placeholder_keyboard(language, "premium"),
    )


@router.callback_query(BuyStates.payment_method, F.data == "b_ps_st")
async def summary_back_stars_amount(query: CallbackQuery, state: FSMContext, language: str, i18n):
    await state.update_data(stars_amount=None, stars_recipient=None)
    await state.set_state(BuyStates.stars_amount)
    await query.message.edit_text(
        i18n("stars_ask_amount"),
        reply_markup=stars_amount_keyboard(language),
    )
    await query.answer()


@router.callback_query(BuyStates.payment_method, F.data == "b_ps_pr")
async def summary_back_premium_recipient(query: CallbackQuery, state: FSMContext, language: str, i18n):
    await state.update_data(premium_recipient=None)
    await state.set_state(BuyStates.premium_recipient)
    await query.message.edit_text(
        i18n("premium_ask_recipient"),
        reply_markup=premium_recipient_keyboard(language),
    )
    await query.answer()