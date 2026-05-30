import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from app.keyboards.main_menu import (
    build_back_to_main_keyboard,
    build_buy_menu_keyboard,
    build_info_keyboard,
    build_main_menu_keyboard,
    build_support_keyboard,
)
from app.keyboards.profile import build_profile_keyboard
from app.keyboards.referral import build_referrals_keyboard, build_referrals_list_keyboard
from app.db.session import session_scope
from app.services.fsm import clear_current_state_only
from app.services.profile import get_profile_stats
from app.services.referral import generate_referral_link
from app.services.referrals import ReferralsService
from app.services.wallet import WalletBindingError, WalletService
from app.states.profile import ProfileWalletState
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
from app.texts.profile import (
    PROFILE_CONNECT_WALLET_INVALID,
    PROFILE_CONNECT_WALLET_PROMPT,
    PROFILE_CONNECT_WALLET_SUCCESS,
    PROFILE_WALLET_DISCONNECTED,
    PROFILE_WALLET_NOT_CONNECTED,
    PROFILE_WALLET_VERIFY_OK,
    PROFILE_WITHDRAW_STARS_ALERT,
    build_profile_text,
)
from app.texts.referral import (
    REFERRAL_WITHDRAW_ALERT,
    build_referrals_list_text,
    build_referrals_text,
)
from app.utils.callbacks import InfoCallbacks, MenuCallbacks, ProfileCallbacks, ReferralCallbacks


router = Router(name="menu")
logger = logging.getLogger(__name__)


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


@router.callback_query(F.data == ProfileCallbacks.CONNECT_WALLET)
async def handle_profile_connect_wallet(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(ProfileWalletState.wallet_address)
    await _edit_callback_message(
        callback,
        PROFILE_CONNECT_WALLET_PROMPT,
        build_profile_keyboard(),
    )


@router.message(ProfileWalletState.wallet_address)
async def handle_profile_connect_wallet_message(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        await state.clear()
        return

    wallet_address = (message.text or "").strip()
    logger.info(
        "wallet_bind_started user_id=%s provider=%s wallet_prefix=%s",
        message.from_user.id,
        "tonkeeper",
        wallet_address[:8],
    )

    async with session_scope() as session:
        wallet_service = WalletService(session)
        try:
            await wallet_service.connect_wallet(
                telegram_id=message.from_user.id,
                wallet_address=wallet_address,
                wallet_provider="tonkeeper",
            )
        except WalletBindingError as error:
            error_message = str(error)
            logger.warning(
                "wallet_bind_rejected user_id=%s provider=%s reason=%s",
                message.from_user.id,
                "tonkeeper",
                error_message,
            )
            if "invalid wallet address" in error_message:
                await message.answer(PROFILE_CONNECT_WALLET_INVALID, reply_markup=build_profile_keyboard())
            elif "already bound" in error_message:
                await message.answer(
                    "Этот кошелек уже привязан к другому аккаунту.",
                    reply_markup=build_profile_keyboard(),
                )
            else:
                await message.answer(
                    "Не удалось привязать кошелек. Повторите попытку.",
                    reply_markup=build_profile_keyboard(),
                )
            return

    logger.info("wallet_bind_success user_id=%s provider=%s", message.from_user.id, "tonkeeper")
    await clear_current_state_only(state)
    stats = await get_profile_stats(message.from_user.id)
    await message.answer(build_profile_text(stats), reply_markup=build_profile_keyboard())
    await message.answer(PROFILE_CONNECT_WALLET_SUCCESS)


@router.callback_query(F.data == ProfileCallbacks.DISCONNECT_WALLET)
async def handle_profile_disconnect_wallet(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await clear_current_state_only(state)
    async with session_scope() as session:
        wallet_service = WalletService(session)
        try:
            await wallet_service.disconnect_wallet(telegram_id=callback.from_user.id)
        except WalletBindingError as error:
            await callback.answer(str(error), show_alert=True)
            return

    logger.info("wallet_disconnect_success user_id=%s", callback.from_user.id)
    stats = await get_profile_stats(callback.from_user.id)
    await _edit_callback_message(callback, build_profile_text(stats), build_profile_keyboard())
    await callback.answer(PROFILE_WALLET_DISCONNECTED, show_alert=True)


@router.callback_query(F.data == ProfileCallbacks.VERIFY_WALLET)
async def handle_profile_verify_wallet(callback: CallbackQuery) -> None:
    await callback.answer()
    async with session_scope() as session:
        wallet_service = WalletService(session)
        try:
            await wallet_service.verify_wallet(telegram_id=callback.from_user.id)
        except WalletBindingError as error:
            logger.warning(
                "wallet_verify_failed user_id=%s reason=%s",
                callback.from_user.id,
                str(error),
            )
            await callback.answer(PROFILE_WALLET_NOT_CONNECTED, show_alert=True)
            return

    logger.info("wallet_verify_success user_id=%s", callback.from_user.id)
    stats = await get_profile_stats(callback.from_user.id)
    await _edit_callback_message(callback, build_profile_text(stats), build_profile_keyboard())
    await callback.answer(PROFILE_WALLET_VERIFY_OK, show_alert=True)


@router.callback_query(F.data == ReferralCallbacks.OPEN)
async def handle_referrals(callback: CallbackQuery) -> None:
    referral_link = await generate_referral_link(callback.from_user.id)
    async with session_scope() as session:
        dashboard = await ReferralsService(session).get_dashboard(callback.from_user.id)
    await callback.answer()
    await _edit_callback_message(
        callback,
        build_referrals_text(
            referral_link,
            referral_count=dashboard.referral_count,
            active_referral_count=dashboard.active_referral_count,
            without_purchase_count=dashboard.without_purchase_count,
            referral_balance=dashboard.referral_balance,
            total_referral_earned=dashboard.total_referral_earned,
        ),
        build_referrals_keyboard(),
    )


@router.callback_query(F.data == ReferralCallbacks.WITHDRAW)
async def handle_referrals_withdraw(callback: CallbackQuery) -> None:
    await callback.answer(REFERRAL_WITHDRAW_ALERT, show_alert=True)


@router.callback_query(F.data == ReferralCallbacks.LIST)
async def handle_referrals_list(callback: CallbackQuery) -> None:
    await _show_referrals_page(callback, page=1)


@router.callback_query(F.data.startswith(f"{ReferralCallbacks.PAGE_PREFIX}:"))
async def handle_referrals_page(callback: CallbackQuery) -> None:
    page_value = callback.data.split(":")[-1] if callback.data else "1"
    page = int(page_value) if page_value.isdigit() else 1
    await _show_referrals_page(callback, page=page)


async def _show_referrals_page(callback: CallbackQuery, *, page: int) -> None:
    async with session_scope() as session:
        referral_page = await ReferralsService(session).get_referral_page(
            callback.from_user.id,
            page=page,
        )

    await callback.answer()
    await _edit_callback_message(
        callback,
        build_referrals_list_text(
            [
                (
                    item.telegram_id,
                    item.username,
                    item.earned_amount,
                    item.is_active,
                )
                for item in referral_page.items
            ],
            current_page=referral_page.current_page,
            total_pages=referral_page.total_pages,
            total_items=referral_page.total_items,
        ),
        build_referrals_list_keyboard(
            current_page=referral_page.current_page,
            total_pages=referral_page.total_pages,
        ),
    )


@router.callback_query(F.data == MenuCallbacks.NEWS)
async def handle_news(callback: CallbackQuery) -> None:
    await callback.answer()
    await _edit_callback_message(callback, NEWS_TEXT, build_back_to_main_keyboard())


@router.callback_query(F.data == MenuCallbacks.PARTNERS)
async def handle_partners(callback: CallbackQuery) -> None:
    await callback.answer()
    await _edit_callback_message(callback, PARTNERS_TEXT, build_back_to_main_keyboard())
