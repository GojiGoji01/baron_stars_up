from aiogram.fsm.context import FSMContext


FSM_KEY_RECIPIENT = "recipient"
FSM_KEY_RECIPIENT_TG_ID = "recipient_tg_id"
FSM_KEY_AMOUNT = "amount"
FSM_KEY_PREMIUM_MONTHS = "premium_months"
FSM_KEY_GIFT_ID = "gift_id"
FSM_KEY_PRODUCT = "product"
FSM_KEY_ORDER_ID = "order_id"
FSM_KEY_INVOICE_ID = "invoice_id"

UNKNOWN_RECIPIENT = "не указан"


def format_telegram_username(username: str | None) -> str:
    if not username:
        return UNKNOWN_RECIPIENT

    username = username.strip()
    if not username:
        return UNKNOWN_RECIPIENT

    return username if username.startswith("@") else f"@{username}"


def get_recipient(data: dict, telegram_username: str | None) -> str:
    recipient = data.get(FSM_KEY_RECIPIENT)
    if recipient:
        return str(recipient)

    return format_telegram_username(telegram_username)


async def get_saved_recipient(state: FSMContext, telegram_username: str | None) -> str:
    data = await state.get_data()
    return get_recipient(data, telegram_username)


async def save_recipient(state: FSMContext, recipient: str) -> None:
    if recipient == UNKNOWN_RECIPIENT:
        return

    await state.update_data(**{FSM_KEY_RECIPIENT: recipient})


async def save_recipient_tg_id(state: FSMContext, recipient_tg_id: int | None) -> None:
    await state.update_data(**{FSM_KEY_RECIPIENT_TG_ID: recipient_tg_id})


async def save_product(state: FSMContext, product: str) -> None:
    await state.update_data(**{FSM_KEY_PRODUCT: product})


async def resolve_self_recipient(state: FSMContext, telegram_username: str | None) -> str:
    telegram_recipient = format_telegram_username(telegram_username)
    if telegram_recipient != UNKNOWN_RECIPIENT:
        return telegram_recipient

    return await get_saved_recipient(state, telegram_username)


async def clear_current_state_only(state: FSMContext) -> None:
    await state.set_state(None)
