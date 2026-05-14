from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from app.keyboards.main_menu import (
    build_back_to_main_keyboard,
    build_buy_menu_keyboard,
    build_info_keyboard,
    build_main_menu_keyboard,
    build_support_keyboard,
)
from app.keyboards.profile import build_profile_keyboard
from app.keyboards.referral import build_referrals_keyboard
from app.services.fsm import clear_current_state_only
from app.services.profile import get_profile_stats
from app.services.referral import generate_referral_link
from app.texts.common import (
    BUY_MENU_TEXT,
    FRANCHISE_TEXT,
    INFO_TEXT,
    NEWS_TEXT,
    OFFER_TEXT,
    PARTNERS_TEXT,
    PRIVACY_TEXT,
    RULES_TEXT,
    START_TEXT,
    SUPPORT_TEXT,
)
from app.texts.profile import PROFILE_WITHDRAW_STARS_ALERT, build_profile_text
from app.texts.referral import REFERRAL_LIST_ALERT, REFERRAL_WITHDRAW_ALERT, build_referrals_text
from app.utils.callbacks import InfoCallbacks, MenuCallbacks, ProfileCallbacks, ReferralCallbacks


router = Router(name="menu")


async def _edit_callback_message(
    callback: CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup,
) -> None:
    if callback.message is None:
        return

    try:
        if callback.message.photo:
            await callback.message.edit_caption(caption=text, reply_markup=reply_markup)
            return

        await callback.message.edit_text(text=text, reply_markup=reply_markup)
    except TelegramBadRequest:
        await callback.message.answer(text=text, reply_markup=reply_markup)


@router.callback_query(F.data == MenuCallbacks.MAIN)
async def handle_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await clear_current_state_only(state)

    await _edit_callback_message(
        callback=callback,
        text=START_TEXT,
        reply_markup=build_main_menu_keyboard(),
    )


@router.callback_query(F.data == MenuCallbacks.BUY)
async def handle_buy_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    await _edit_callback_message(callback, BUY_MENU_TEXT, build_buy_menu_keyboard())


@router.callback_query(F.data == MenuCallbacks.HELP)
async def handle_help(callback: CallbackQuery) -> None:
    await callback.answer()
    await _edit_callback_message(callback, SUPPORT_TEXT, build_support_keyboard())


@router.callback_query(F.data == MenuCallbacks.SUPPORT)
async def handle_support(callback: CallbackQuery) -> None:
    await callback.answer()
    await _edit_callback_message(callback, SUPPORT_TEXT, build_support_keyboard())


@router.callback_query(F.data == MenuCallbacks.INFO)
async def handle_info(callback: CallbackQuery) -> None:
    await callback.answer()
    await _edit_callback_message(callback, INFO_TEXT, build_info_keyboard())


@router.callback_query(F.data == InfoCallbacks.RULES)
async def handle_rules(callback: CallbackQuery) -> None:
    await callback.answer()
    await _edit_callback_message(callback, RULES_TEXT, build_info_keyboard())


@router.callback_query(F.data == InfoCallbacks.PRIVACY)
async def handle_privacy(callback: CallbackQuery) -> None:
    await callback.answer()
    await _edit_callback_message(callback, PRIVACY_TEXT, build_info_keyboard())


@router.callback_query(F.data == InfoCallbacks.OFFER)
async def handle_offer(callback: CallbackQuery) -> None:
    await callback.answer()
    await _edit_callback_message(callback, OFFER_TEXT, build_info_keyboard())


@router.callback_query(F.data == InfoCallbacks.FRANCHISE)
async def handle_franchise(callback: CallbackQuery) -> None:
    await callback.answer()
    await _edit_callback_message(callback, FRANCHISE_TEXT, build_info_keyboard())


@router.callback_query(F.data == ProfileCallbacks.OPEN)
async def handle_profile(callback: CallbackQuery) -> None:
    stats = await get_profile_stats(callback.from_user.id)
    await callback.answer()
    await _edit_callback_message(
        callback,
        build_profile_text(stats),
        build_profile_keyboard(),
    )


@router.callback_query(F.data == ProfileCallbacks.WITHDRAW_STARS)
async def handle_profile_withdraw_stars(callback: CallbackQuery) -> None:
    await callback.answer(PROFILE_WITHDRAW_STARS_ALERT, show_alert=True)


@router.callback_query(F.data == ReferralCallbacks.OPEN)
async def handle_referrals(callback: CallbackQuery) -> None:
    referral_link = await generate_referral_link(callback.from_user.id)
    await callback.answer()
    await _edit_callback_message(
        callback,
        build_referrals_text(referral_link),
        build_referrals_keyboard(),
    )


@router.callback_query(F.data == ReferralCallbacks.WITHDRAW)
async def handle_referrals_withdraw(callback: CallbackQuery) -> None:
    await callback.answer(REFERRAL_WITHDRAW_ALERT, show_alert=True)


@router.callback_query(F.data == ReferralCallbacks.LIST)
async def handle_referrals_list(callback: CallbackQuery) -> None:
    await callback.answer(REFERRAL_LIST_ALERT, show_alert=True)


@router.callback_query(F.data == MenuCallbacks.NEWS)
async def handle_news(callback: CallbackQuery) -> None:
    await callback.answer()
    await _edit_callback_message(callback, NEWS_TEXT, build_back_to_main_keyboard())


@router.callback_query(F.data == MenuCallbacks.PARTNERS)
async def handle_partners(callback: CallbackQuery) -> None:
    await callback.answer()
    await _edit_callback_message(callback, PARTNERS_TEXT, build_back_to_main_keyboard())
