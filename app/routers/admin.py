from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.db.models.order import Order
from app.db.session import session_scope
from app.services.admin import AdminService
from app.services.checkout import CheckoutError, retry_delivery
from app.services.orders import OrdersService
from app.utils.telegram import safe_answer_callback
from config import settings


router = Router(name="admin")

ADMIN_CALLBACK_PREFIX = "admin:"
ADMIN_COMPLETE_PREFIX = "admin:complete:"
ADMIN_ERROR_PREFIX = "admin:error:"
ADMIN_REFUND_PREFIX = "admin:refund:"
ADMIN_RETRY_PREFIX = "admin:retry:"


def _is_admin(user_id: int) -> bool:
    admin_ids = set(settings.admin_owner_ids) | set(settings.admin_manager_ids)
    return user_id in admin_ids


def _get_order_username(order: Order) -> str:
    username = getattr(order, "username", None)
    if not username:
        return "not set"
    return f"@{username.lstrip('@')}"


def _get_order_item(order: Order) -> str:
    return str(getattr(order, "item", None) or getattr(order, "order_type", None) or "not set")


def _format_order(order: Order) -> str:
    username = _get_order_username(order)
    item = _get_order_item(order)
    amount = getattr(order, "amount_rub", None)

    return (
        f"<b>Order #{order.id}</b>\n"
        f"User: <code>{order.user_id}</code>\n"
        f"Username: {escape(username)}\n"
        f"Item: {escape(item)}\n"
        f"Amount: <b>{amount} RUB</b>\n"
        f"Status: <code>{escape(order.status)}</code>"
    )


def _get_order_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Completed",
                    callback_data=f"{ADMIN_COMPLETE_PREFIX}{order_id}",
                ),
                InlineKeyboardButton(
                    text="Error",
                    callback_data=f"{ADMIN_ERROR_PREFIX}{order_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Refund request",
                    callback_data=f"{ADMIN_REFUND_PREFIX}{order_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Retry delivery",
                    callback_data=f"{ADMIN_RETRY_PREFIX}{order_id}",
                )
            ],
        ]
    )


async def _send_orders(message: Message, orders: list[Order]) -> None:
    if not orders:
        await message.answer("Admin area\n\nNo orders yet.")
        return

    await message.answer("Admin area\n\nRecent orders:")
    for order in orders:
        await message.answer(
            _format_order(order),
            reply_markup=_get_order_keyboard(order.id),
            parse_mode="HTML",
        )


@router.message(Command("admin"))
async def handle_admin(message: Message) -> None:
    if message.from_user is None or not _is_admin(message.from_user.id):
        await message.answer("Access denied.")
        return

    async with session_scope() as session:
        orders_service = OrdersService(session)
        admin_service = AdminService(session)
        orders = await admin_service.list_orders(limit=10)

        for order in orders:
            await orders_service.update_status(order.id, order.status)

    await _send_orders(message, orders)


@router.callback_query(F.data.startswith(ADMIN_CALLBACK_PREFIX))
async def handle_admin_order_action(callback: CallbackQuery) -> None:
    if callback.from_user is None or not _is_admin(callback.from_user.id):
        await safe_answer_callback(callback, "Access denied.", show_alert=True)
        return

    if callback.data is None:
        await safe_answer_callback(callback, "Invalid action.", show_alert=True)
        return

    action, order_id = _parse_admin_callback(callback.data)
    if action is None or order_id is None:
        await safe_answer_callback(callback, "Invalid action.", show_alert=True)
        return

    async with session_scope() as session:
        orders_service = OrdersService(session)
        admin_service = AdminService(session)

        if action == "complete":
            order = await admin_service.complete_order(order_id)
        elif action == "error":
            order = await admin_service.mark_failed(order_id)
        elif action == "refund":
            try:
                order = await admin_service.refund_request(order_id)
            except ValueError as error:
                await safe_answer_callback(callback, str(error), show_alert=True)
                return
        elif action == "retry":
            try:
                result = await retry_delivery(session, order_id=order_id)
            except CheckoutError as error:
                await safe_answer_callback(callback, str(error), show_alert=True)
                return
            order = result.order
        else:
            order = None

        if order is not None:
            await orders_service.update_status(order.id, order.status)

    if order is None:
        await safe_answer_callback(callback, "Order not found.", show_alert=True)
        return

    if callback.message is not None:
        await callback.message.edit_text(
            _format_order(order),
            reply_markup=_get_order_keyboard(order.id),
            parse_mode="HTML",
        )
    await safe_answer_callback(callback, "Status updated.")


def _parse_admin_callback(callback_data: str) -> tuple[str | None, int | None]:
    parts = callback_data.split(":")
    if len(parts) != 3 or parts[0] != "admin":
        return None, None

    try:
        return parts[1], int(parts[2])
    except ValueError:
        return None, None
