from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from app.keyboards.common import build_custom_amount_keyboard, build_payment_method_keyboard
from app.keyboards.gifts import build_gift_list_keyboard, build_gift_recipient_keyboard
from app.keyboards.premium import build_premium_duration_keyboard, build_premium_target_keyboard
from app.keyboards.sell import build_sell_stars_keyboard
from app.keyboards.stars import build_stars_amount_keyboard, build_stars_recipient_keyboard
from app.keyboards.ton import build_ton_amount_keyboard
from app.services.fsm import (
    FSM_KEY_AMOUNT,
    FSM_KEY_GIFT_ID,
    FSM_KEY_PREMIUM_MONTHS,
    UNKNOWN_RECIPIENT,
    clear_current_state_only,
    get_recipient,
    get_saved_recipient,
    resolve_self_recipient,
    save_recipient,
)
from app.services.gifts import get_gift_price
from app.services.orders import OrderStatus, create_order, update_order_status
from app.services.payments.ton import TonPaymentProvider
from app.services.pricing import (
    SELL_STARS_MAX_AMOUNT,
    SELL_STARS_MIN_AMOUNT,
    STARS_MAX_AMOUNT,
    STARS_MIN_AMOUNT,
    calculate_star_price,
    calculate_sell_price,
    validate_sell_stars_amount,
    validate_stars_amount,
)
from app.services.recipient import normalize_username
from app.states.order import GiftOrder, PremiumOrder, SellStarsOrder, StarsOrder, TonOrder
from app.texts.common import (
    INVALID_AMOUNT_TEXT,
    INVALID_DURATION_TEXT,
    INVALID_QUANTITY_TEXT,
    PAYMENT_MOCK_TEXT,
    USERNAME_INVALID_TEXT,
)
from app.texts.gifts import (
    GIFT_PREVIEW_TEXT,
    gift_enter_recipient_text,
    gift_list_text,
    gift_payment_text,
    gift_unknown_recipient_text,
)
from app.texts.payment import (
    payment_gift_text,
    payment_invoice_text,
    payment_premium_text,
    payment_stars_text,
    payment_ton_text,
)
from app.texts.premium import (
    premium_duration_text,
    premium_enter_recipient_text,
    premium_payment_text,
    premium_self_already_active_alert,
    premium_target_text,
    premium_unknown_recipient_text,
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
from app.texts.ton import (
    TON_AMOUNT_NUMBER_REQUIRED_TEXT,
    TON_AMOUNT_POSITIVE_TEXT,
    TON_PREVIEW_TEXT,
    ton_enter_amount_text,
    ton_payment_text,
)
from app.utils.callbacks import (
    BuyCallbacks,
    GiftCallbacks,
    MenuCallbacks,
    PaymentCallbacks,
    PremiumCallbacks,
    SellCallbacks,
    StarsCallbacks,
    TonCallbacks,
)


router = Router(name="buy")
ton_payment_provider = TonPaymentProvider()


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
    await state.update_data(product="stars")
    await save_recipient(state, recipient)

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
    await state.update_data(product="stars")

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

    await state.update_data(product="stars")
    await save_recipient(state, recipient)
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
    await state.update_data(product="stars", **{FSM_KEY_AMOUNT: amount})
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
    await state.update_data(product="stars", **{FSM_KEY_AMOUNT: amount})
    await clear_current_state_only(state)
    await message.answer(
        stars_payment_text(recipient, amount),
        reply_markup=build_payment_method_keyboard(StarsCallbacks.AMOUNT_BACK),
    )


@router.callback_query(F.data == BuyCallbacks.PREMIUM)
async def handle_premium_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await clear_current_state_only(state)
    await state.update_data(product="premium")

    await _edit_callback_message(
        callback=callback,
        text=premium_duration_text(),
        reply_markup=build_premium_duration_keyboard(),
    )


@router.callback_query(F.data == PremiumCallbacks.TARGET_BACK)
async def handle_premium_target_back(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    premium_months = int(data.get(FSM_KEY_PREMIUM_MONTHS, 3))
    await clear_current_state_only(state)
    await callback.answer()

    await _edit_callback_message(
        callback=callback,
        text=premium_target_text(premium_months),
        reply_markup=build_premium_target_keyboard(),
    )


@router.callback_query(F.data.startswith(f"{PremiumCallbacks.DURATION_PREFIX}:"))
async def handle_premium_duration_target(callback: CallbackQuery, state: FSMContext) -> None:
    premium_months_value = callback.data.split(":")[-1] if callback.data else ""

    if not premium_months_value.isdigit():
        await callback.answer(INVALID_DURATION_TEXT, show_alert=True)
        return

    premium_months = int(premium_months_value)
    await state.update_data(product="premium", **{FSM_KEY_PREMIUM_MONTHS: premium_months})
    await callback.answer()

    await _edit_callback_message(
        callback=callback,
        text=premium_target_text(premium_months),
        reply_markup=build_premium_target_keyboard(),
    )


@router.callback_query(F.data == PremiumCallbacks.SELF)
async def handle_premium_self(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.is_premium:
        await callback.answer(premium_self_already_active_alert(), show_alert=True)
        return

    data = await state.get_data()
    premium_months = int(data.get(FSM_KEY_PREMIUM_MONTHS, 3))
    recipient = await resolve_self_recipient(state, callback.from_user.username)

    if recipient == UNKNOWN_RECIPIENT:
        await callback.answer()
        await state.set_state(PremiumOrder.recipient)
        await _edit_callback_message(
            callback=callback,
            text=premium_unknown_recipient_text(premium_months),
            reply_markup=build_custom_amount_keyboard(PremiumCallbacks.TARGET_BACK),
        )
        return

    await state.update_data(product="premium")
    await save_recipient(state, recipient)
    await clear_current_state_only(state)
    await callback.answer()
    await _edit_callback_message(
        callback=callback,
        text=premium_payment_text(premium_months, recipient),
        reply_markup=build_payment_method_keyboard(PremiumCallbacks.TARGET_BACK),
    )


@router.callback_query(F.data == PremiumCallbacks.FRIEND)
async def handle_premium_friend(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(PremiumOrder.recipient)
    await state.update_data(product="premium")

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

    data = await state.get_data()
    premium_months = int(data.get(FSM_KEY_PREMIUM_MONTHS, 3))
    await state.update_data(product="premium")
    await save_recipient(state, recipient)
    await clear_current_state_only(state)
    await message.answer(
        premium_payment_text(premium_months, recipient),
        reply_markup=build_payment_method_keyboard(PremiumCallbacks.TARGET_BACK),
    )


@router.callback_query(F.data == BuyCallbacks.TON)
async def handle_ton_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await clear_current_state_only(state)
    await state.update_data(product="ton")
    await _edit_callback_message(callback, TON_PREVIEW_TEXT, build_ton_amount_keyboard())


@router.callback_query(F.data.startswith(f"{TonCallbacks.AMOUNT_PREFIX}:"))
async def handle_ton_amount(callback: CallbackQuery, state: FSMContext) -> None:
    amount_value = callback.data.split(":")[-1] if callback.data else ""

    if amount_value == "custom":
        await callback.answer()
        await state.set_state(TonOrder.custom_amount)
        await _edit_callback_message(
            callback,
            ton_enter_amount_text(),
            build_custom_amount_keyboard(BuyCallbacks.TON),
        )
        return

    if not amount_value.isdigit():
        await callback.answer(INVALID_AMOUNT_TEXT, show_alert=True)
        return

    amount = int(amount_value)
    await state.update_data(product="ton", **{FSM_KEY_AMOUNT: amount})
    await callback.answer()
    await _edit_callback_message(
        callback,
        ton_payment_text(amount),
        build_payment_method_keyboard(BuyCallbacks.TON),
    )


@router.message(TonOrder.custom_amount)
async def handle_ton_custom_amount(message: Message, state: FSMContext) -> None:
    amount_text = (message.text or "").strip().replace(",", ".")

    try:
        amount = float(amount_text)
    except ValueError:
        await message.answer(TON_AMOUNT_NUMBER_REQUIRED_TEXT, reply_markup=build_custom_amount_keyboard(BuyCallbacks.TON))
        return

    if amount <= 0:
        await message.answer(TON_AMOUNT_POSITIVE_TEXT, reply_markup=build_custom_amount_keyboard(BuyCallbacks.TON))
        return

    await state.update_data(product="ton", **{FSM_KEY_AMOUNT: amount})
    await clear_current_state_only(state)
    await message.answer(
        ton_payment_text(amount),
        reply_markup=build_payment_method_keyboard(BuyCallbacks.TON),
    )


@router.callback_query(F.data == BuyCallbacks.GIFT)
async def handle_gift_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await clear_current_state_only(state)
    await state.update_data(product="gift")
    await _edit_callback_message(callback, GIFT_PREVIEW_TEXT, build_gift_recipient_keyboard())


@router.callback_query(F.data == GiftCallbacks.SELF)
async def handle_gift_self(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    recipient = await resolve_self_recipient(state, callback.from_user.username)
    await state.update_data(product="gift")
    await save_recipient(state, recipient)

    if recipient == UNKNOWN_RECIPIENT:
        await state.set_state(GiftOrder.recipient)
        await _edit_callback_message(
            callback,
            gift_unknown_recipient_text(),
            build_custom_amount_keyboard(BuyCallbacks.GIFT),
        )
        return

    await _edit_callback_message(callback, gift_list_text(recipient), build_gift_list_keyboard())


@router.callback_query(F.data == GiftCallbacks.FRIEND)
async def handle_gift_friend(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(GiftOrder.recipient)
    await state.update_data(product="gift")
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

    await state.update_data(product="gift")
    await save_recipient(state, recipient)
    await clear_current_state_only(state)
    await message.answer(gift_list_text(recipient), reply_markup=build_gift_list_keyboard())


@router.callback_query(F.data.startswith(f"{GiftCallbacks.SELECT_PREFIX}:"))
async def handle_gift_item(callback: CallbackQuery, state: FSMContext) -> None:
    gift_id = int(callback.data.split(":")[-1]) if callback.data else 0
    amount = await get_gift_price(gift_id)
    data = await state.get_data()
    recipient = get_recipient(data, callback.from_user.username)
    await state.update_data(product="gift", **{FSM_KEY_GIFT_ID: gift_id, FSM_KEY_AMOUNT: amount})
    await callback.answer()
    await _edit_callback_message(
        callback,
        gift_payment_text(recipient, amount),
        build_payment_method_keyboard(BuyCallbacks.GIFT),
    )


@router.callback_query(F.data == SellCallbacks.STARS)
async def handle_sell_stars_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await clear_current_state_only(state)
    await state.update_data(product="sell_stars")
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
    await state.update_data(product="sell_stars", **{FSM_KEY_AMOUNT: amount})
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
    await state.update_data(product="sell_stars", **{FSM_KEY_AMOUNT: amount})
    await clear_current_state_only(state)
    await message.answer(
        sell_stars_summary_text(amount, payout),
        reply_markup=build_custom_amount_keyboard(SellCallbacks.STARS),
    )


@router.callback_query(F.data == PaymentCallbacks.TON)
async def handle_payment_ton(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    product = data.get("product", "order")
    await callback.answer()

    if product == "stars":
        recipient = get_recipient(data, callback.from_user.username)
        amount = int(data.get(FSM_KEY_AMOUNT, 0))
        price = await calculate_star_price(amount)
        text = payment_stars_text(recipient=recipient, amount=amount)
    elif product == "premium":
        recipient = get_recipient(data, callback.from_user.username)
        amount = int(data.get(FSM_KEY_PREMIUM_MONTHS, 3))
        price = amount
        text = payment_premium_text(recipient=recipient, premium_months=amount)
    elif product == "ton":
        recipient = get_recipient(data, callback.from_user.username)
        amount = data.get(FSM_KEY_AMOUNT, 0)
        price = amount
        text = payment_ton_text(amount)
    elif product == "gift":
        recipient = get_recipient(data, callback.from_user.username)
        amount = int(data.get(FSM_KEY_AMOUNT, 0))
        price = amount
        text = payment_gift_text(recipient=recipient, amount=amount)
    else:
        text = PAYMENT_MOCK_TEXT
        await _edit_callback_message(callback, text, build_payment_method_keyboard(MenuCallbacks.MAIN))
        return

    order = await create_order(
        user_id=callback.from_user.id,
        order_type=str(product),
        recipient=recipient,
        amount=amount,
        price=price,
        payment_method=ton_payment_provider.payment_method,
        status=OrderStatus.CREATED,
    )
    await update_order_status(order.order_id, OrderStatus.PENDING_PAYMENT)
    invoice = await ton_payment_provider.create_invoice(order)
    await state.update_data(order_id=order.order_id, invoice_id=invoice.invoice_id)
    text = f"{text}\n\n{payment_invoice_text(order, invoice)}"

    await _edit_callback_message(callback, text, build_payment_method_keyboard(MenuCallbacks.MAIN))
