from app.texts.common import PAYMENT_MOCK_TEXT
from app.services.orders import Order
from app.services.payments.base import PaymentInvoice


def payment_stars_text(recipient: str, amount: int) -> str:
    return (
        "Оплата TON\n\n"
        "Продукт: Telegram Stars\n"
        f"👤 Получатель: {recipient}\n"
        f"⭐️ Количество: {amount}\n\n"
        f"{PAYMENT_MOCK_TEXT}"
    )


def payment_premium_text(recipient: str, premium_months: int) -> str:
    return (
        "Оплата TON\n\n"
        "Продукт: Telegram Premium\n"
        f"⚜️ Срок: {premium_months} мес.\n"
        f"👤 Получатель: {recipient}\n\n"
        f"{PAYMENT_MOCK_TEXT}"
    )


def payment_ton_text(amount: int | float) -> str:
    return (
        "Оплата TON\n\n"
        "Продукт: TON\n"
        f"💎 Количество: {amount} TON\n\n"
        f"{PAYMENT_MOCK_TEXT}"
    )


def payment_gift_text(recipient: str, amount: int) -> str:
    return (
        "Оплата TON\n\n"
        "Продукт: Telegram Gift\n"
        f"Получатель: {recipient}\n"
        f"Стоимость: {amount} ₽\n\n"
        f"{PAYMENT_MOCK_TEXT}"
    )


def payment_invoice_text(order: Order, invoice: PaymentInvoice) -> str:
    return (
        "Оплата создана\n\n"
        f"Номер заказа: {order.order_id}\n"
        f"Тип заказа: {order.order_type}\n"
        f"Получатель: {order.recipient}\n"
        f"Количество: {order.amount}\n"
        f"Цена: {order.price} ₽\n"
        f"Способ оплаты: {order.payment_method.upper()}\n"
        f"Статус: {order.status}\n\n"
        f"Mock invoice: {invoice.invoice_id}\n"
        f"Mock link: {invoice.pay_url}"
    )
