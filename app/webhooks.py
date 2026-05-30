import asyncio
import logging
from typing import Any

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import session_scope
from app.repositories.orders import OrderStatus
from app.services.checkout import CheckoutBlockedError, CheckoutError, confirm_payment_and_deliver
from app.services.orders import OrdersService
from app.services.payments.base import PaymentProviderError, PaymentStatus
from app.services.payments.crypto import CryptoPaymentProvider
from app.services.payments.platega_sbp import PlategaSbpPaymentProvider
from config import settings


logger = logging.getLogger(__name__)

TELEGRAM_SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token"
PLATEGA_MERCHANT_HEADER = "X-MerchantId"
PLATEGA_SECRET_HEADER = "X-Secret"
CRYPTOBOT_SECRET_HEADERS = (
    "X-CryptoBot-Webhook-Secret",
    "X-Crypto-Pay-Webhook-Secret",
)
FINAL_ORDER_STATUSES = {
    OrderStatus.COMPLETED.value,
    OrderStatus.FAILED.value,
    OrderStatus.CANCELED.value,
    OrderStatus.REFUNDED.value,
}


def create_webhook_app(bot: Bot, dispatcher: Dispatcher) -> web.Application:
    app = web.Application()
    app["bot"] = bot
    app["dispatcher"] = dispatcher

    app.router.add_get("/health", handle_health)
    app.router.add_post(settings.telegram_webhook_path, handle_telegram_webhook)
    app.router.add_post(settings.platega_webhook_path, handle_platega_webhook)
    app.router.add_post(settings.cryptobot_webhook_path, handle_cryptobot_webhook)

    return app


async def run_webhook_server(bot: Bot, dispatcher: Dispatcher) -> None:
    _validate_webhook_settings()
    await _set_telegram_webhook(bot)

    app = create_webhook_app(bot, dispatcher)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=settings.webhook_host, port=settings.webhook_port)
    await site.start()
    logger.info(
        "webhook_server_started host=%s port=%s base_url=%s",
        settings.webhook_host,
        settings.webhook_port,
        settings.webhook_base_url,
    )

    try:
        await asyncio.Event().wait()
    finally:
        if settings.telegram_delete_webhook_on_shutdown:
            await bot.delete_webhook(drop_pending_updates=False)
            logger.info("telegram_webhook_deleted_on_shutdown")
        await runner.cleanup()


async def handle_health(request: web.Request) -> web.Response:
    return web.json_response({"ok": True, "mode": settings.bot_mode})


async def handle_telegram_webhook(request: web.Request) -> web.Response:
    if not _is_valid_telegram_secret(request):
        logger.warning("telegram_webhook_rejected reason=invalid_secret")
        return web.json_response({"ok": False}, status=403)

    try:
        payload = await request.json()
        update = Update.model_validate(payload, context={"bot": request.app["bot"]})
    except Exception:
        logger.exception("telegram_webhook_invalid_payload")
        return web.json_response({"ok": False}, status=400)

    try:
        await request.app["dispatcher"].feed_update(request.app["bot"], update)
    except Exception:
        logger.exception(
            "telegram_webhook_dispatch_error update_id=%s",
            payload.get("update_id"),
        )
    return web.json_response({"ok": True})


async def handle_platega_webhook(request: web.Request) -> web.Response:
    if not _is_valid_platega_headers(request):
        logger.warning("platega_webhook_rejected reason=invalid_headers")
        return web.json_response({"ok": False}, status=403)

    try:
        payload = await request.json()
    except Exception:
        logger.exception("platega_webhook_invalid_json")
        return web.json_response({"ok": False}, status=400)

    logger.info(
        "platega_webhook_received status=%s transaction_id=%s order_id=%s keys=%s",
        _extract_first(payload, "status", "paymentStatus"),
        _extract_transaction_id(payload),
        _extract_order_id(payload),
        sorted(payload.keys()),
    )
    asyncio.create_task(_process_payment_webhook("platega", payload))
    return web.json_response({"ok": True})


async def handle_cryptobot_webhook(request: web.Request) -> web.Response:
    if not _is_valid_cryptobot_secret(request):
        logger.warning("cryptobot_webhook_rejected reason=invalid_secret")
        return web.json_response({"ok": False}, status=403)

    try:
        payload = await request.json()
    except Exception:
        logger.exception("cryptobot_webhook_invalid_json")
        return web.json_response({"ok": False}, status=400)

    invoice = _extract_cryptobot_invoice(payload)
    logger.info(
        "cryptobot_webhook_received status=%s invoice_id=%s payload=%s keys=%s",
        invoice.get("status"),
        invoice.get("invoice_id"),
        invoice.get("payload"),
        sorted(payload.keys()),
    )
    asyncio.create_task(_process_payment_webhook("cryptobot", payload))
    return web.json_response({"ok": True})


async def _process_payment_webhook(provider: str, payload: dict[str, Any]) -> None:
    try:
        async with session_scope() as session:
            orders_service = OrdersService(session)
            order = await _find_order_from_payload(orders_service, provider, payload)
            if order is None:
                logger.warning(
                    "payment_webhook_order_not_found provider=%s transaction_id=%s order_id=%s",
                    provider,
                    _extract_transaction_id(payload),
                    _extract_order_id(payload),
                )
                return

            if order.status == OrderStatus.COMPLETED.value:
                logger.info(
                    "payment_webhook_idempotent_completed provider=%s order_id=%s",
                    provider,
                    order.order_id,
                )
                return

            payment_status = _normalize_payment_status(provider, payload)
            logger.info(
                "payment_webhook_processing provider=%s order_id=%s db_id=%s payment_status=%s current_status=%s",
                provider,
                order.order_id,
                order.id,
                payment_status,
                order.status,
            )

            if payment_status == "paid":
                await confirm_payment_and_deliver(session, order_id=order.id)
                return

            if payment_status in {"canceled", "refunded", "failed"}:
                await _recheck_and_apply_non_paid_status(
                    session=session,
                    orders_service=orders_service,
                    order=order,
                    webhook_status=payment_status,
                )
    except CheckoutBlockedError as error:
        logger.warning("payment_webhook_blocked provider=%s message=%s", provider, error.safe_message)
    except CheckoutError:
        logger.exception("payment_webhook_checkout_error provider=%s", provider)
    except PaymentProviderError:
        logger.exception("payment_webhook_provider_recheck_failed provider=%s", provider)
    except Exception:
        logger.exception("payment_webhook_unhandled_error provider=%s", provider)


async def _recheck_and_apply_non_paid_status(
    *,
    session: AsyncSession,
    orders_service: OrdersService,
    order,
    webhook_status: str,
) -> None:
    if not order.payment_transaction_id:
        logger.warning(
            "payment_webhook_non_paid_without_transaction order_id=%s webhook_status=%s",
            order.id,
            webhook_status,
        )
        return

    provider = _get_payment_provider(order.payment_provider)
    recheck_result = await provider.check_payment(order.payment_transaction_id)
    logger.info(
        "payment_webhook_non_paid_recheck order_id=%s webhook_status=%s provider_status=%s is_paid=%s",
        order.id,
        webhook_status,
        recheck_result.status,
        recheck_result.is_paid,
    )

    if recheck_result.is_paid:
        await confirm_payment_and_deliver(session, order_id=order.id)
        return

    provider_status = recheck_result.status
    if webhook_status == "refunded" or provider_status == PaymentStatus.REFUNDED.value:
        await orders_service.update_status(order.id, OrderStatus.REFUNDED.value)
        return
    if webhook_status == "canceled" or provider_status == PaymentStatus.CANCELED.value:
        await orders_service.update_status(order.id, OrderStatus.CANCELED.value)
        return
    if webhook_status == "failed" or provider_status == PaymentStatus.FAILED.value:
        await orders_service.update_status(order.id, OrderStatus.FAILED.value)
        return

    logger.info(
        "payment_webhook_non_paid_recheck_ignored order_id=%s webhook_status=%s provider_status=%s",
        order.id,
        webhook_status,
        provider_status,
    )


async def _find_order_from_payload(
    orders_service: OrdersService,
    provider: str,
    payload: dict[str, Any],
):
    if provider == "cryptobot":
        invoice = _extract_cryptobot_invoice(payload)
        transaction_id = str(invoice.get("invoice_id") or "")
        order_id = str(invoice.get("payload") or "")
    else:
        transaction_id = _extract_transaction_id(payload)
        order_id = _extract_order_id(payload)

    if transaction_id:
        order = await orders_service.get_order_by_payment_transaction_id(transaction_id)
        if order is not None:
            return order

    if order_id:
        if order_id.isdigit():
            order = await orders_service.get_order_by_id(int(order_id))
            if order is not None:
                return order

        return await orders_service.get_order_by_order_id(order_id)

    return None


def _validate_webhook_settings() -> None:
    if not settings.webhook_base_url:
        raise RuntimeError("WEBHOOK_BASE_URL is required in webhook mode")
    if not settings.telegram_webhook_secret:
        raise RuntimeError("TELEGRAM_WEBHOOK_SECRET is required in webhook mode")


async def _set_telegram_webhook(bot: Bot) -> None:
    webhook_url = f"{settings.webhook_base_url.rstrip('/')}{settings.telegram_webhook_path}"
    await bot.set_webhook(
        webhook_url,
        secret_token=settings.telegram_webhook_secret,
        allowed_updates=["message", "callback_query"],
    )
    logger.info("telegram_webhook_set url=%s", webhook_url)


def _is_valid_telegram_secret(request: web.Request) -> bool:
    return request.headers.get(TELEGRAM_SECRET_HEADER) == settings.telegram_webhook_secret


def _is_valid_platega_headers(request: web.Request) -> bool:
    return (
        request.headers.get(PLATEGA_MERCHANT_HEADER) == settings.platega_merchant_id
        and request.headers.get(PLATEGA_SECRET_HEADER) == settings.platega_secret
    )


def _is_valid_cryptobot_secret(request: web.Request) -> bool:
    if not settings.cryptobot_webhook_secret:
        return False

    for header_name in CRYPTOBOT_SECRET_HEADERS:
        if request.headers.get(header_name) == settings.cryptobot_webhook_secret:
            return True

    authorization = request.headers.get("Authorization", "")
    if authorization == f"Bearer {settings.cryptobot_webhook_secret}":
        return True

    return request.query.get("secret") == settings.cryptobot_webhook_secret


def _get_payment_provider(provider_name: str | None):
    if provider_name == CryptoPaymentProvider.provider_name:
        return CryptoPaymentProvider()
    return PlategaSbpPaymentProvider()


def _normalize_payment_status(provider: str, payload: dict[str, Any]) -> str:
    if provider == "cryptobot":
        invoice = _extract_cryptobot_invoice(payload)
        status = str(invoice.get("status", "")).lower()
        if status == "paid":
            return "paid"
        if status in {"refunded", "refund", "chargeback"}:
            return "refunded"
        if status in {"deleted", "expired", "canceled", "cancelled"}:
            return "canceled"
        if status in {"failed", "error"}:
            return "failed"
        return "pending"

    status = str(_extract_first(payload, "status", "paymentStatus") or "").lower()
    if status in {"confirmed", "success", "succeeded", "completed", "paid"}:
        return "paid"
    if status in {"canceled", "cancelled"}:
        return "canceled"
    if status in {"chargeback", "refunded", "refund"}:
        return "refunded"
    if status in {"failed", "error", "declined"}:
        return "failed"
    return "pending"


def _extract_cryptobot_invoice(payload: dict[str, Any]) -> dict[str, Any]:
    payload_body = payload.get("payload")
    if isinstance(payload_body, dict):
        return payload_body

    result = payload.get("result")
    if isinstance(result, dict):
        return result

    return payload


def _extract_transaction_id(payload: dict[str, Any]) -> str:
    value = _extract_first(
        payload,
        "transactionId",
        "transaction_id",
        "id",
        "invoice_id",
        "paymentTransactionId",
    )
    return str(value or "")


def _extract_order_id(payload: dict[str, Any]) -> str:
    value = _extract_first(
        payload,
        "payload",
        "orderId",
        "order_id",
        "merchantOrderId",
    )
    return str(value or "")


def _extract_first(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = payload.get(key)
        if value is not None:
            return value
    return None
