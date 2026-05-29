from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from decimal import Decimal
import asyncio
import logging

from app.keyboards.common import (
    build_custom_amount_keyboard,
    build_payment_method_keyboard,
    build_payment_url_keyboard,
)
from app.keyboards.gifts import build_gift_list_keyboard, build_gift_recipient_keyboard
from app.keyboards.premium import build_premium_duration_keyboard, build_premium_target_keyboard
from app.keyboards.sell import build_sell_stars_keyboard
from app.keyboards.stars import build_stars_amount_keyboard, build_stars_recipient_keyboard
from app.db.session import session_scope
from app.services.checkout import CheckoutBlockedError, CheckoutError, confirm_payment_and_deliver
from app.services.fsm import (
    FSM_KEY_AMOUNT,
    FSM_KEY_GIFT_ID,
    FSM_KEY_INVOICE_ID,
    FSM_KEY_ORDER_ID,
    FSM_KEY_PREMIUM_MONTHS,
    FSM_KEY_PRODUCT,
    FSM_KEY_RECIPIENT_TG_ID,
    UNKNOWN_RECIPIENT,
    clear_current_state_only,
    get_recipient,
    get_saved_recipient,
    resolve_self_recipient,
    save_product,
    save_recipient,
    save_recipient_tg_id,
)
from app.services.gifts import get_available_gifts, get_gift_item
from app.services.orders import OrderStatus, OrdersService
from app.services.payments.base import PaymentProviderError
from app.services.payments.crypto import CryptoPaymentProvider
from app.services.payments.platega_sbp import PlategaSbpPaymentProvider
from app.services.pricing import (
    SELL_STARS_MAX_AMOUNT,
    SELL_STARS_MIN_AMOUNT,
    STARS_MAX_AMOUNT,
    STARS_MIN_AMOUNT,
    calculate_premium_price,
    calculate_star_price,
    calculate_sbp_price,
    calculate_sell_price,
    validate_sell_stars_amount,
    validate_stars_amount,
)
from app.services.recipient import normalize_username
from app.states.order import GiftOrder, PremiumOrder, SellStarsOrder, StarsOrder
from app.texts.common import (
    INVALID_AMOUNT_TEXT,
    INVALID_DURATION_TEXT,
    INVALID_QUANTITY_TEXT,
    PAYMENT_MOCK_TEXT,
    USERNAME_INVALID_TEXT,
)
from app.texts.gifts import (
    GIFT_PREVIEW_TEXT,
    GIFTS_UNAVAILABLE_TEXT,
    gift_enter_recipient_text,
    gift_enter_recipient_tg_id_text,
    gift_list_text,
    gift_payment_text,
    gift_recipient_tg_id_invalid_text,
    gift_unknown_recipient_text,
)
from app.texts.payment import (
    SBP_RECIPIENT_TG_ID_REQUIRED_TEXT,
    gift_sbp_invoice_created_text,
    payment_gift_text,
    payment_invoice_text,
    payment_premium_text,
    premium_sbp_invoice_created_text,
    sbp_invoice_created_text,
    payment_stars_text,
)
from app.texts.premium import (
    premium_duration_text,
    premium_enter_recipient_text,
    premium_enter_recipient_tg_id_text,
    premium_payment_text,
    premium_recipient_tg_id_invalid_text,
    premium_self_already_active_alert,
    premium_start_text,
)
from app.texts.sell import (
    SELL_STARS_NUMBER_REQUIRED_TEXT,
    SELL_STARS_TEXT,
    sell_stars_range_text,
    sell_stars_summary_text,
)
from app.texts.stars import (
    stars_amount_number_required_text,
    stars_amount_range_text,
    stars_amount_text,
    stars_custom_amount_text,
    stars_enter_recipient_text,
    stars_payment_text,
    stars_recipient_choice_text,
    stars_unknown_recipient_text,
)
from app.utils.callbacks import (
    BuyCallbacks,
    GiftCallbacks,
    MenuCallbacks,
    PaymentCallbacks,
    PremiumCallbacks,
    SellCallbacks,
    StarsCallbacks,
)


router = Router(name="buy")
logger = logging.getLogger(__name__)

crypto_payment_provider = CryptoPaymentProvider()
sbp_payment_provider = PlategaSbpPaymentProvider()
INVOICE_CREATE_RETRY_ATTEMPTS = 3
INVOICE_CREATE_RETRY_DELAY_SECONDS = 1.0


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


async def _normalize_recipient_or_warn(
    message: Message,
    back_callback_data: str,
) -> str | None:
    recipient = await normalize_username(message.text or "")

    if recipient is None:
        await message.answer(
            USERNAME_INVALID_TEXT,
            reply_markup=build_custom_amount_keyboard(back_callback_data),
        )
        return None

    return recipient


@router.callback_query(F.data == BuyCallbacks.STARS)
async def handle_stars_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await clear_current_state_only(state)

    await _edit_callback_message(
        callback=callback,
        text=stars_recipient_choice_text(),
        reply_markup=build_stars_recipient_keyboard(),
    )


@router.callback_query(F.data == StarsCallbacks.SELF)
async def handle_stars_self(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()

    recipient = await resolve_self_recipient(state, callback.from_user.username)
    await save_product(state, "stars")
    await save_recipient(state, recipient)
    await save_recipient_tg_id(state, callback.from_user.id)

    if recipient == UNKNOWN_RECIPIENT:
        await state.set_state(StarsOrder.recipient)
        await _edit_callback_message(
            callback=callback,
            text=stars_unknown_recipient_text(),
            reply_markup=build_custom_amount_keyboard(BuyCallbacks.STARS),
        )
        return

    await clear_current_state_only(state)
    await _edit_callback_message(
        callback=callback,
        text=stars_amount_text(recipient),
        reply_markup=build_stars_amount_keyboard(),
    )


@router.callback_query(F.data == StarsCallbacks.FRIEND)
async def handle_stars_friend(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(StarsOrder.recipient)
    await save_product(state, "stars")
    await save_recipient_tg_id(state, None)

    await _edit_callback_message(
        callback=callback,
        text=stars_enter_recipient_text(),
        reply_markup=build_custom_amount_keyboard(BuyCallbacks.STARS),
    )


@router.message(StarsOrder.recipient)
async def handle_stars_manual_recipient(message: Message, state: FSMContext) -> None:
    recipient = await _normalize_recipient_or_warn(message, BuyCallbacks.STARS)
    if recipient is None:
        return

    await save_product(state, "stars")
    await save_recipient(state, recipient)
    await save_recipient_tg_id(state, None)
    await clear_current_state_only(state)
    await message.answer(stars_amount_text(recipient), reply_markup=build_stars_amount_keyboard())


@router.callback_query(F.data.startswith(f"{StarsCallbacks.AMOUNT_PREFIX}:"))
async def handle_stars_amount(callback: CallbackQuery, state: FSMContext) -> None:
    amount_value = callback.data.split(":")[-1] if callback.data else ""
    recipient = await get_saved_recipient(state, callback.from_user.username)

    if recipient == UNKNOWN_RECIPIENT:
        await callback.answer()
        await state.set_state(StarsOrder.recipient)
        await _edit_callback_message(
            callback=callback,
            text=stars_unknown_recipient_text(),
            reply_markup=build_custom_amount_keyboard(BuyCallbacks.STARS),
        )
        return

    if amount_value == "back":
        await callback.answer()
        await clear_current_state_only(state)
        await _edit_callback_message(callback, stars_amount_text(recipient), build_stars_amount_keyboard())
        return

    if amount_value == "custom":
        await callback.answer()
        await state.set_state(StarsOrder.custom_amount)
        await _edit_callback_message(
            callback=callback,
            text=stars_custom_amount_text(recipient, STARS_MIN_AMOUNT, STARS_MAX_AMOUNT),
            reply_markup=build_custom_amount_keyboard(),
        )
        return

    if not amount_value.isdigit():
        await callback.answer(INVALID_AMOUNT_TEXT, show_alert=True)
        return

    amount = int(amount_value)
    await save_product(state, "stars")
    await state.update_data(**{FSM_KEY_AMOUNT: amount})
    await callback.answer()
    await _edit_callback_message(
        callback=callback,
        text=stars_payment_text(recipient, amount),
        reply_markup=build_payment_method_keyboard(StarsCallbacks.AMOUNT_BACK),
    )


@router.message(StarsOrder.custom_amount)
async def handle_stars_custom_amount(message: Message, state: FSMContext) -> None:
    amount_text = (message.text or "").strip()

    if not amount_text.isdigit():
        await message.answer(stars_amount_number_required_text(), reply_markup=build_custom_amount_keyboard())
        return

    amount = int(amount_text)
    if not await validate_stars_amount(amount):
        await message.answer(
            stars_amount_range_text(STARS_MIN_AMOUNT, STARS_MAX_AMOUNT),
            reply_markup=build_custom_amount_keyboard(),
        )
        return

    recipient = await get_saved_recipient(state, message.from_user.username if message.from_user else None)
    await save_product(state, "stars")
    await state.update_data(**{FSM_KEY_AMOUNT: amount})
    await clear_current_state_only(state)
    await message.answer(
        stars_payment_text(recipient, amount),
        reply_markup=build_payment_method_keyboard(StarsCallbacks.AMOUNT_BACK),
    )


@router.callback_query(F.data == BuyCallbacks.PREMIUM)
async def handle_premium_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await clear_current_state_only(state)
    await save_product(state, "premium")

    await _edit_callback_message(
        callback=callback,
        text=premium_start_text(),
        reply_markup=build_premium_target_keyboard(),
    )


@router.callback_query(F.data == PremiumCallbacks.TARGET_BACK)
async def handle_premium_target_back(callback: CallbackQuery, state: FSMContext) -> None:
    await clear_current_state_only(state)
    await callback.answer()

    await _edit_callback_message(
        callback=callback,
        text=premium_start_text(),
        reply_markup=build_premium_target_keyboard(),
    )


@router.callback_query(F.data == PremiumCallbacks.DURATION_BACK)
async def handle_premium_duration_back(callback: CallbackQuery, state: FSMContext) -> None:
    await clear_current_state_only(state)
    await callback.answer()

    await _edit_callback_message(
        callback=callback,
        text=premium_duration_text(),
        reply_markup=build_premium_duration_keyboard(),
    )


@router.callback_query(F.data.startswith(f"{PremiumCallbacks.DURATION_PREFIX}:"))
async def handle_premium_duration_target(callback: CallbackQuery, state: FSMContext) -> None:
    premium_months_value = callback.data.split(":")[-1] if callback.data else ""

    if not premium_months_value.isdigit():
        await callback.answer(INVALID_DURATION_TEXT, show_alert=True)
        return

    premium_months = int(premium_months_value)
    data = await state.get_data()
    recipient = get_recipient(data, callback.from_user.username)
    await save_product(state, "premium")
    await state.update_data(**{FSM_KEY_PREMIUM_MONTHS: premium_months})
    await callback.answer()

    await _edit_callback_message(
        callback=callback,
        text=premium_payment_text(premium_months, recipient),
        reply_markup=build_payment_method_keyboard(PremiumCallbacks.DURATION_BACK),
    )


@router.callback_query(F.data == PremiumCallbacks.SELF)
async def handle_premium_self(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.is_premium:
        await callback.answer(premium_self_already_active_alert(), show_alert=True)
        return

    recipient = await resolve_self_recipient(state, callback.from_user.username)

    if recipient == UNKNOWN_RECIPIENT:
        await callback.answer()
        await state.set_state(PremiumOrder.recipient)
        await _edit_callback_message(
            callback=callback,
            text=premium_enter_recipient_text(),
            reply_markup=build_custom_amount_keyboard(PremiumCallbacks.TARGET_BACK),
        )
        return

    await save_product(state, "premium")
    await save_recipient(state, recipient)
    await save_recipient_tg_id(state, callback.from_user.id)
    await clear_current_state_only(state)
    await callback.answer()
    await _edit_callback_message(
        callback=callback,
        text=premium_duration_text(),
        reply_markup=build_premium_duration_keyboard(),
    )


@router.callback_query(F.data == PremiumCallbacks.FRIEND)
async def handle_premium_friend(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(PremiumOrder.recipient)
    await save_product(state, "premium")
    await save_recipient_tg_id(state, None)

    await _edit_callback_message(
        callback=callback,
        text=premium_enter_recipient_text(),
        reply_markup=build_custom_amount_keyboard(PremiumCallbacks.TARGET_BACK),
    )


@router.message(PremiumOrder.recipient)
async def handle_premium_friend_recipient(message: Message, state: FSMContext) -> None:
    recipient = await _normalize_recipient_or_warn(message, PremiumCallbacks.TARGET_BACK)
    if recipient is None:
        return

    await save_product(state, "premium")
    await save_recipient(state, recipient)
    await save_recipient_tg_id(state, None)
    await state.set_state(PremiumOrder.recipient_tg_id)
    await message.answer(
        premium_enter_recipient_tg_id_text(recipient),
        reply_markup=build_custom_amount_keyboard(PremiumCallbacks.FRIEND),
    )


@router.message(PremiumOrder.recipient_tg_id)
async def handle_premium_friend_recipient_tg_id(message: Message, state: FSMContext) -> None:
    recipient_tg_id_text = (message.text or "").strip()
    if not recipient_tg_id_text.isdigit():
        await message.answer(
            premium_recipient_tg_id_invalid_text(),
            reply_markup=build_custom_amount_keyboard(PremiumCallbacks.FRIEND),
        )
        return

    await save_product(state, "premium")
    await save_recipient_tg_id(state, int(recipient_tg_id_text))
    await clear_current_state_only(state)
    await message.answer(
        premium_duration_text(),
        reply_markup=build_premium_duration_keyboard(),
    )


@router.callback_query(F.data == BuyCallbacks.GIFT)
async def handle_gift_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await clear_current_state_only(state)
    await save_product(state, "gift")
    await _edit_callback_message(callback, GIFT_PREVIEW_TEXT, build_gift_recipient_keyboard())


@router.callback_query(F.data == GiftCallbacks.SELF)
async def handle_gift_self(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    recipient = await resolve_self_recipient(state, callback.from_user.username)
    await save_product(state, "gift")
    await save_recipient(state, recipient)
    await save_recipient_tg_id(state, callback.from_user.id)

    if recipient == UNKNOWN_RECIPIENT:
        await state.set_state(GiftOrder.recipient)
        await _edit_callback_message(
            callback,
            gift_unknown_recipient_text(),
            build_custom_amount_keyboard(BuyCallbacks.GIFT),
        )
        return

    gifts = await get_available_gifts()
    if not gifts:
        await _edit_callback_message(callback, GIFTS_UNAVAILABLE_TEXT, build_custom_amount_keyboard(BuyCallbacks.GIFT))
        return

    await _edit_callback_message(callback, gift_list_text(recipient), build_gift_list_keyboard(gifts))


@router.callback_query(F.data == GiftCallbacks.FRIEND)
async def handle_gift_friend(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(GiftOrder.recipient)
    await save_product(state, "gift")
    await _edit_callback_message(
        callback,
        gift_enter_recipient_text(),
        build_custom_amount_keyboard(BuyCallbacks.GIFT),
    )


@router.message(GiftOrder.recipient)
async def handle_gift_manual_recipient(message: Message, state: FSMContext) -> None:
    recipient = await _normalize_recipient_or_warn(message, BuyCallbacks.GIFT)
    if recipient is None:
        return

    data = await state.get_data()
    existing_recipient_tg_id = data.get(FSM_KEY_RECIPIENT_TG_ID)
    await save_product(state, "gift")
    await save_recipient(state, recipient)
    if existing_recipient_tg_id is None:
        await state.set_state(GiftOrder.recipient_tg_id)
        await message.answer(
            gift_enter_recipient_tg_id_text(recipient),
            reply_markup=build_custom_amount_keyboard(GiftCallbacks.FRIEND),
        )
        return

    await clear_current_state_only(state)
    gifts = await get_available_gifts()
    if not gifts:
        await message.answer(GIFTS_UNAVAILABLE_TEXT, reply_markup=build_custom_amount_keyboard(BuyCallbacks.GIFT))
        return

    await message.answer(gift_list_text(recipient), reply_markup=build_gift_list_keyboard(gifts))


@router.message(GiftOrder.recipient_tg_id)
async def handle_gift_manual_recipient_tg_id(message: Message, state: FSMContext) -> None:
    recipient_tg_id_text = (message.text or "").strip()
    if not recipient_tg_id_text.isdigit():
        await message.answer(
            gift_recipient_tg_id_invalid_text(),
            reply_markup=build_custom_amount_keyboard(GiftCallbacks.FRIEND),
        )
        return

    await save_product(state, "gift")
    await save_recipient_tg_id(state, int(recipient_tg_id_text))
    await clear_current_state_only(state)
    data = await state.get_data()
    recipient = get_recipient(data, message.from_user.username if message.from_user else None)
    gifts = await get_available_gifts()
    if not gifts:
        await message.answer(GIFTS_UNAVAILABLE_TEXT, reply_markup=build_custom_amount_keyboard(BuyCallbacks.GIFT))
        return

    await message.answer(gift_list_text(recipient), reply_markup=build_gift_list_keyboard(gifts))


@router.callback_query(F.data.startswith(f"{GiftCallbacks.SELECT_PREFIX}:"))
async def handle_gift_item(callback: CallbackQuery, state: FSMContext) -> None:
    gift_id = int(callback.data.split(":")[-1]) if callback.data else 0
    try:
        gift_item = await get_gift_item(gift_id)
    except ValueError:
        await callback.answer("Подарок недоступен. Обновите список.", show_alert=True)
        return
    amount = gift_item.price
    data = await state.get_data()
    recipient = get_recipient(data, callback.from_user.username)
    await save_product(state, "gift")
    await state.update_data(**{FSM_KEY_GIFT_ID: gift_id, FSM_KEY_AMOUNT: amount})
    await callback.answer()
    await _edit_callback_message(
        callback,
        gift_payment_text(recipient, amount, gift_emoji=gift_item.emoji),
        build_payment_method_keyboard(BuyCallbacks.GIFT),
    )


@router.callback_query(F.data == SellCallbacks.STARS)
async def handle_sell_stars_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await clear_current_state_only(state)
    await save_product(state, "sell_stars")
    await _edit_callback_message(callback, SELL_STARS_TEXT, build_sell_stars_keyboard())


@router.callback_query(F.data.startswith(f"{SellCallbacks.AMOUNT_PREFIX}:"))
async def handle_sell_stars_amount(callback: CallbackQuery, state: FSMContext) -> None:
    amount_value = callback.data.split(":")[-1] if callback.data else ""

    if amount_value == "custom":
        await callback.answer()
        await state.set_state(SellStarsOrder.amount)
        await _edit_callback_message(callback, SELL_STARS_TEXT, build_custom_amount_keyboard(SellCallbacks.STARS))
        return

    if not amount_value.isdigit():
        await callback.answer(INVALID_QUANTITY_TEXT, show_alert=True)
        return

    amount = int(amount_value)
    payout = await calculate_sell_price(amount)
    await save_product(state, "sell_stars")
    await state.update_data(**{FSM_KEY_AMOUNT: amount})
    await callback.answer()
    await _edit_callback_message(
        callback,
        sell_stars_summary_text(amount, payout),
        build_custom_amount_keyboard(SellCallbacks.STARS),
    )


@router.message(SellStarsOrder.amount)
async def handle_sell_stars_custom_amount(message: Message, state: FSMContext) -> None:
    amount_text = (message.text or "").strip()

    if not amount_text.isdigit():
        await message.answer(SELL_STARS_NUMBER_REQUIRED_TEXT, reply_markup=build_custom_amount_keyboard(SellCallbacks.STARS))
        return

    amount = int(amount_text)
    if not await validate_sell_stars_amount(amount):
        await message.answer(
            sell_stars_range_text(SELL_STARS_MIN_AMOUNT, SELL_STARS_MAX_AMOUNT),
            reply_markup=build_custom_amount_keyboard(SellCallbacks.STARS),
        )
        return

    payout = await calculate_sell_price(amount)
    await save_product(state, "sell_stars")
    await state.update_data(**{FSM_KEY_AMOUNT: amount})
    await clear_current_state_only(state)
    await message.answer(
        sell_stars_summary_text(amount, payout),
        reply_markup=build_custom_amount_keyboard(SellCallbacks.STARS),
    )


@router.callback_query(F.data.in_({PaymentCallbacks.SBP, PaymentCallbacks.CRYPTO}))
async def handle_payment_method(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    product = data.get(FSM_KEY_PRODUCT, "order")
    payment_callback = callback.data or PaymentCallbacks.SBP
    await callback.answer()

    if product == "stars":
        recipient = get_recipient(data, callback.from_user.username)
        amount = int(data.get(FSM_KEY_AMOUNT, 0))
        price = await calculate_star_price(amount)
        text = payment_stars_text(recipient=recipient, amount=amount)
    elif product == "premium":
        recipient = get_recipient(data, callback.from_user.username)
        amount = int(data.get(FSM_KEY_PREMIUM_MONTHS, 3))
        price = await calculate_premium_price(amount)
        text = payment_premium_text(recipient=recipient, premium_months=amount)
    elif product == "gift":
        recipient = get_recipient(data, callback.from_user.username)
        gift_id = data.get(FSM_KEY_GIFT_ID)
        if gift_id is None:
            await _edit_callback_message(
                callback,
                "Подарок не выбран. Пожалуйста, выберите подарок заново.",
                build_custom_amount_keyboard(BuyCallbacks.GIFT),
            )
            return

        try:
            gift_item = await get_gift_item(gift_id, force_refresh=True)
        except ValueError:
            await _edit_callback_message(
                callback,
                "Выбранный подарок больше недоступен. Обновите список и выберите другой.",
                build_custom_amount_keyboard(BuyCallbacks.GIFT),
            )
            return

        amount = gift_item.price
        price = gift_item.price
        text = payment_gift_text(
            recipient=recipient,
            amount=amount,
            gift_emoji=gift_item.emoji,
        )
    else:
        text = PAYMENT_MOCK_TEXT
        await _edit_callback_message(callback, text, build_payment_method_keyboard(MenuCallbacks.MAIN))
        return

    payment_method = _get_payment_method_name(payment_callback)
    if payment_callback == PaymentCallbacks.SBP and data.get(FSM_KEY_RECIPIENT_TG_ID) is None:
        await _edit_callback_message(
            callback,
            SBP_RECIPIENT_TG_ID_REQUIRED_TEXT,
            build_payment_method_keyboard(MenuCallbacks.MAIN),
        )
        return

    async with session_scope() as session:
        orders_service = OrdersService(session)
        order = await orders_service.create_order(
            user_id=callback.from_user.id,
            amount_rub=Decimal(str(price)),
            cost_price=Decimal("0.00"),
            status=OrderStatus.CREATED.value,
            order_type=str(product),
            recipient=recipient,
            recipient_tg_id=data.get(FSM_KEY_RECIPIENT_TG_ID),
            gift_id=str(data.get(FSM_KEY_GIFT_ID)) if product == "gift" and data.get(FSM_KEY_GIFT_ID) is not None else None,
            amount=amount,
            price_rub=Decimal(str(price)),
            payment_provider=payment_method,
        )

        try:
            invoice = await _create_invoice_for_payment_method(
                payment_callback=payment_callback,
                order=order,
                state_data=data,
            )
        except PaymentProviderError:
            await orders_service.update_status(order.id, OrderStatus.FAILED.value)
            await _edit_callback_message(
                callback,
                "Не удалось создать счет на оплату. Попробуйте другой способ оплаты или повторите позже.",
                build_payment_method_keyboard(MenuCallbacks.MAIN),
            )
            return

        order = await orders_service.update_order(
            order.id,
            status=OrderStatus.PENDING_PAYMENT.value,
            payment_provider=invoice.provider,
            payment_transaction_id=invoice.transaction_id,
            payment_url=invoice.payment_url,
        ) or order

    await state.update_data(**{FSM_KEY_ORDER_ID: order.id, FSM_KEY_INVOICE_ID: invoice.invoice_id})
    if payment_callback == PaymentCallbacks.SBP:
        await _send_sbp_invoice_message(callback, order, invoice)
        return

    text = f"{text}\n\n{payment_invoice_text(order, invoice)}"

    await _edit_callback_message(
        callback,
        text,
        build_payment_url_keyboard(
            invoice.payment_url,
            check_callback_data=PaymentCallbacks.check(order.id),
        ),
    )


@router.callback_query(F.data.startswith(f"{PaymentCallbacks.CHECK_PREFIX}:"))
async def handle_payment_check(callback: CallbackQuery) -> None:
    order_id_value = callback.data.split(":")[-1] if callback.data else ""
    if not order_id_value.isdigit():
        await callback.answer("Некорректный номер заказа.", show_alert=True)
        return

    try:
        async with session_scope() as session:
            result = await confirm_payment_and_deliver(session, order_id=int(order_id_value))
    except CheckoutBlockedError as error:
        await callback.answer(error.safe_message, show_alert=True)
        return
    except (CheckoutError, PaymentProviderError):
        logger.exception("payment_check_failed order_id=%s", order_id_value)
        await callback.answer("Не удалось проверить оплату. Попробуйте позже.", show_alert=True)
        return

    if result.payment_status == "paid":
        message = result.user_message or "Оплата подтверждена."
        await callback.answer(message, show_alert=True)
        return

    await callback.answer("Оплата пока не найдена. Попробуйте немного позже.", show_alert=True)


def _get_payment_method_name(payment_callback: str) -> str:
    if payment_callback == PaymentCallbacks.SBP:
        return sbp_payment_provider.provider_name
    return crypto_payment_provider.payment_method


async def _create_invoice_for_payment_method(
    *,
    payment_callback: str,
    order,
    state_data: dict,
):
    if payment_callback == PaymentCallbacks.SBP:
        recipient_tg_id = state_data.get(FSM_KEY_RECIPIENT_TG_ID)
        if recipient_tg_id is None:
            raise ValueError("recipient_tg_id is required for SBP")

        sbp_price = await calculate_sbp_price(order.price_rub)
        return await _create_sbp_invoice_with_retry(
            order=order,
            recipient_tg_id=int(recipient_tg_id),
            amount_rub=Decimal(str(sbp_price)),
        )

    if payment_callback == PaymentCallbacks.CRYPTO:
        return await crypto_payment_provider.create_invoice(order)
    raise PaymentProviderError("Unsupported payment method")


async def _create_sbp_invoice_with_retry(*, order, recipient_tg_id: int, amount_rub: Decimal):
    last_error: PaymentProviderError | None = None

    for attempt in range(1, INVOICE_CREATE_RETRY_ATTEMPTS + 1):
        try:
            logger.info(
                "sbp_invoice_create_attempt order_id=%s attempt=%s",
                order.order_id,
                attempt,
            )
            return await sbp_payment_provider.create_invoice(
                amount_rub=amount_rub,
                order_id=order.order_id,
                recipient_tg_id=recipient_tg_id,
                payload=order.order_id,
            )
        except PaymentProviderError as error:
            last_error = error
            logger.warning(
                "sbp_invoice_create_retry order_id=%s attempt=%s error_type=%s",
                order.order_id,
                attempt,
                type(error).__name__,
            )
            if attempt < INVOICE_CREATE_RETRY_ATTEMPTS:
                await asyncio.sleep(INVOICE_CREATE_RETRY_DELAY_SECONDS * attempt)

    raise last_error or PaymentProviderError("Unable to create SBP invoice")


async def _send_sbp_invoice_message(callback: CallbackQuery, order, invoice) -> None:
    if callback.message is None:
        return

    logger.info(
        "sbp_invoice_created order_id=%s transaction_id=%s amount=%s",
        order.order_id,
        invoice.transaction_id,
        invoice.amount,
    )
    if order.order_type == "premium":
        invoice_text = premium_sbp_invoice_created_text(order, invoice)
    elif order.order_type == "gift":
        gift_title: str | None = None
        if order.gift_id is not None:
            try:
                gift_item = await get_gift_item(order.gift_id)
            except ValueError:
                gift_item = None
            if gift_item is not None:
                gift_title = gift_item.display_title
        invoice_text = gift_sbp_invoice_created_text(order, invoice, gift_title=gift_title)
    else:
        invoice_text = sbp_invoice_created_text(order, invoice)

    await callback.message.answer(
        text=invoice_text,
        reply_markup=build_payment_url_keyboard(
            invoice.payment_url,
            check_callback_data=PaymentCallbacks.check(order.id),
        ),
        parse_mode="HTML",
    )
