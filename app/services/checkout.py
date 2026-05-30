import logging
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.order import Order
from app.repositories.orders import DeliveryStatus, OrderStatus
from app.services.antifraud import (
    ANTIFRAUD_BLOCKED_MESSAGE,
    AntifraudService,
)
from app.services.fragment import FragmentDeliveryStatus, FragmentService
from app.services.gift_delivery import GiftDeliveryService
from app.services.orders import OrdersService
from app.services.payments.base import PaymentProviderError, PaymentStatus
from app.services.payments.crypto import CryptoPaymentProvider
from app.services.payments.platega_sbp import PlategaSbpPaymentProvider
from app.services.pricing import calculate_star_price
from app.services.referrals import ReferralsService


logger = logging.getLogger(__name__)

FRAGMENT_DISABLED_BUY_MESSAGE = (
    "Оплата получена, но Fragment backend не смог выполнить покупку Stars: "
    "Buy button is disabled. Проверьте аккаунт Fragment, TON balance, wallet "
    "session, cookies/localStorage или внешний automation backend."
)
FRAGMENT_DELIVERY_FAILED_MESSAGE = (
    "Оплата получена, но автоматическая выдача не завершилась. "
    "Заказ сохранен, потребуется проверка."
)
FRAGMENT_DELIVERY_PENDING_MESSAGE = "Оплата получена, выдача поставлена в обработку."
PREMIUM_DELIVERY_PENDING_MESSAGE = "Оплата получена, Premium ожидает обработки."
GIFT_DELIVERY_FAILED_MESSAGE = (
    "Оплата получена, но не удалось определить подарок для отправки."
)


class CheckoutError(Exception):
    pass


class CheckoutBlockedError(CheckoutError):
    def __init__(self, safe_message: str = ANTIFRAUD_BLOCKED_MESSAGE) -> None:
        self.safe_message = safe_message
        super().__init__(safe_message)


@dataclass(frozen=True)
class StarsCheckoutResult:
    order: Order
    payment_url: str


@dataclass(frozen=True)
class PaymentDeliveryResult:
    order: Order
    payment_status: str
    delivery_status: str | None
    user_message: str | None = None


class CheckoutService:
    def __init__(
        self,
        session: AsyncSession,
        payment_provider: PlategaSbpPaymentProvider | None = None,
        crypto_payment_provider: CryptoPaymentProvider | None = None,
        fragment_service: FragmentService | None = None,
        antifraud_service: AntifraudService | None = None,
    ) -> None:
        self.orders_service = OrdersService(session)
        self.payment_provider = payment_provider or PlategaSbpPaymentProvider()
        self.crypto_payment_provider = crypto_payment_provider or CryptoPaymentProvider()
        self.fragment_service = fragment_service or FragmentService()
        self.gift_delivery_service = GiftDeliveryService()
        self.antifraud_service = antifraud_service or AntifraudService()
        self.referrals_service = ReferralsService(session)

    async def create_stars_checkout(
        self,
        *,
        user_id: int,
        recipient: str,
        recipient_tg_id: int,
        amount: int,
    ) -> StarsCheckoutResult:
        antifraud_result = await self.antifraud_service.check_recipient(
            recipient=recipient,
            recipient_tg_id=recipient_tg_id,
            user_id=user_id,
        )
        if not antifraud_result.is_allowed:
            raise CheckoutBlockedError()

        price_rub = Decimal(str(await calculate_star_price(amount)))
        order = await self.orders_service.create_stars_order(
            user_id=user_id,
            recipient=recipient,
            recipient_tg_id=recipient_tg_id,
            amount=amount,
            price_rub=price_rub,
            status=OrderStatus.PENDING.value,
        )

        try:
            invoice = await self.payment_provider.create_invoice(
                amount_rub=price_rub,
                order_id=order.order_id or str(order.id),
                recipient_tg_id=recipient_tg_id,
                payload=str(order.id),
            )
        except PaymentProviderError:
            await self.orders_service.update_status(order.id, OrderStatus.FAILED.value)
            raise

        updated_order = await self.orders_service.update_order(
            order.id,
            payment_provider=invoice.provider,
            payment_transaction_id=invoice.transaction_id,
            payment_url=invoice.payment_url,
            status=OrderStatus.PENDING_PAYMENT.value,
        )
        if updated_order is None:
            raise CheckoutError("Order disappeared after invoice creation")

        logger.info(
            "stars_checkout_created order_id=%s user_id=%s recipient_tg_id=%s amount=%s provider=%s",
            updated_order.id,
            user_id,
            recipient_tg_id,
            amount,
            invoice.provider,
        )
        return StarsCheckoutResult(order=updated_order, payment_url=invoice.payment_url)

    async def create_gift_checkout(
        self,
        *,
        user_id: int,
        recipient: str,
        recipient_tg_id: int,
        gift_id: str,
        price_rub: Decimal,
    ) -> StarsCheckoutResult:
        antifraud_result = await self.antifraud_service.check_recipient(
            recipient=recipient,
            recipient_tg_id=recipient_tg_id,
            user_id=user_id,
        )
        if not antifraud_result.is_allowed:
            raise CheckoutBlockedError()

        order = await self.orders_service.create_gift_order(
            user_id=user_id,
            recipient=recipient,
            recipient_tg_id=recipient_tg_id,
            gift_id=gift_id,
            price_rub=price_rub,
            status=OrderStatus.PENDING.value,
        )

        try:
            invoice = await self.payment_provider.create_invoice(
                amount_rub=price_rub,
                order_id=order.order_id or str(order.id),
                recipient_tg_id=recipient_tg_id,
                payload=str(order.id),
            )
        except PaymentProviderError:
            await self.orders_service.update_status(order.id, OrderStatus.FAILED.value)
            raise

        updated_order = await self.orders_service.update_order(
            order.id,
            payment_provider=invoice.provider,
            payment_transaction_id=invoice.transaction_id,
            payment_url=invoice.payment_url,
            status=OrderStatus.PENDING_PAYMENT.value,
        )
        if updated_order is None:
            raise CheckoutError("Order disappeared after invoice creation")

        logger.info(
            "gift_checkout_created order_id=%s user_id=%s recipient_tg_id=%s gift_id=%s provider=%s",
            updated_order.id,
            user_id,
            recipient_tg_id,
            gift_id,
            invoice.provider,
        )
        return StarsCheckoutResult(order=updated_order, payment_url=invoice.payment_url)

    async def confirm_payment_and_deliver(self, *, order_id: int) -> PaymentDeliveryResult:
        order = await self.orders_service.get_order_by_id(order_id)
        if order is None:
            raise CheckoutError("Order not found")
        logger.info(
            "confirm_payment_started order_id=%s status=%s payment_provider=%s payment_transaction_id=%s",
            order.id,
            order.status,
            order.payment_provider,
            order.payment_transaction_id,
        )

        if order.status == OrderStatus.COMPLETED.value:
            return PaymentDeliveryResult(
                order=order,
                payment_status=PaymentStatus.PAID.value,
                delivery_status=order.delivery_status,
            )

        if not order.payment_transaction_id:
            raise CheckoutError("Order has no payment transaction")

        antifraud_result = await self.antifraud_service.check_recipient(
            recipient=order.recipient,
            recipient_tg_id=order.recipient_tg_id,
            user_id=order.user_id,
        )
        if not antifraud_result.is_allowed:
            await self.orders_service.update_order(
                order.id,
                status=OrderStatus.FAILED.value,
                delivery_status=DeliveryStatus.FAILED.value,
            )
            raise CheckoutBlockedError()

        payment_provider = self._get_payment_provider(order.payment_provider)
        payment_result = await payment_provider.check_payment(order.payment_transaction_id)
        logger.info(
            "confirm_payment_provider_result order_id=%s provider=%s payment_status=%s is_paid=%s",
            order.id,
            order.payment_provider,
            payment_result.status,
            payment_result.is_paid,
        )
        if not payment_result.is_paid:
            return PaymentDeliveryResult(
                order=order,
                payment_status=payment_result.status,
                delivery_status=order.delivery_status,
            )

        if order.status not in {OrderStatus.PAID.value, OrderStatus.COMPLETED.value}:
            order = await self.orders_service.update_status(order.id, OrderStatus.PAID.value) or order

        return await self._deliver_paid_order(order=order, payment_status=payment_result.status)

    async def retry_delivery(self, *, order_id: int) -> PaymentDeliveryResult:
        order = await self.orders_service.get_order_by_id(order_id)
        if order is None:
            raise CheckoutError("Order not found")

        if order.status == OrderStatus.COMPLETED.value:
            return PaymentDeliveryResult(
                order=order,
                payment_status=PaymentStatus.PAID.value,
                delivery_status=order.delivery_status,
            )

        if order.status not in {
            OrderStatus.PAID.value,
            OrderStatus.DELIVERY_PENDING.value,
            OrderStatus.DELIVERY_FAILED.value,
        }:
            raise CheckoutError("Retry delivery is allowed only for paid orders")

        return await self._deliver_paid_order(order=order, payment_status=PaymentStatus.PAID.value)

    async def _deliver_paid_order(
        self,
        *,
        order: Order,
        payment_status: str,
    ) -> PaymentDeliveryResult:
        if order.delivery_status == FragmentDeliveryStatus.COMPLETED.value:
            return PaymentDeliveryResult(
                order=order,
                payment_status=payment_status,
                delivery_status=order.delivery_status,
            )

        order = await self.orders_service.orders.increment_delivery_attempts(order.id) or order
        logger.info(
            "delivery_started order_id=%s order_type=%s payment_status=%s delivery_attempts=%s",
            order.id,
            order.order_type,
            payment_status,
            order.delivery_attempts,
        )
        if order.order_type == "premium":
            order = await self.orders_service.update_order(
                order.id,
                status=OrderStatus.DELIVERY_PENDING.value,
                delivery_status=FragmentDeliveryStatus.PENDING.value,
            ) or order
            return PaymentDeliveryResult(
                order=order,
                payment_status=payment_status,
                delivery_status=FragmentDeliveryStatus.PENDING.value,
                user_message=PREMIUM_DELIVERY_PENDING_MESSAGE,
            )

        if order.order_type == "gift":
            if not order.gift_id:
                order = await self.orders_service.update_order(
                    order.id,
                    status=OrderStatus.DELIVERY_FAILED.value,
                    delivery_status=FragmentDeliveryStatus.FAILED.value,
                ) or order
                return PaymentDeliveryResult(
                    order=order,
                    payment_status=payment_status,
                    delivery_status=FragmentDeliveryStatus.FAILED.value,
                    user_message=GIFT_DELIVERY_FAILED_MESSAGE,
                )

            delivery_result = await self.gift_delivery_service.send_gift(
                order_id=order.order_id or str(order.id),
                recipient_tg_id=int(order.recipient_tg_id or 0),
                gift_id=str(order.gift_id),
            )
        else:
            delivery_result = await self.fragment_service.buy_stars(order)
        logger.info(
            "delivery_result order_id=%s order_type=%s success=%s retryable=%s transaction_id=%s raw_keys=%s",
            order.id,
            order.order_type,
            delivery_result.is_success,
            delivery_result.is_retryable,
            delivery_result.transaction_id,
            sorted(delivery_result.raw.keys()) if isinstance(delivery_result.raw, dict) else [],
        )

        if delivery_result.is_success:
            order = await self.orders_service.update_order(
                order.id,
                status=OrderStatus.COMPLETED.value,
                delivery_status=FragmentDeliveryStatus.COMPLETED.value,
                fragment_transaction_id=delivery_result.transaction_id,
            ) or order
            await self.referrals_service.accrue_after_completed(order)
            return PaymentDeliveryResult(
                order=order,
                payment_status=payment_status,
                delivery_status=FragmentDeliveryStatus.COMPLETED.value,
            )

        if delivery_result.is_retryable:
            order = await self.orders_service.update_order(
                order.id,
                status=OrderStatus.DELIVERY_PENDING.value,
                delivery_status=FragmentDeliveryStatus.PENDING.value,
                fragment_transaction_id=delivery_result.transaction_id,
            ) or order
            return PaymentDeliveryResult(
                order=order,
                payment_status=payment_status,
                delivery_status=FragmentDeliveryStatus.PENDING.value,
                user_message=FRAGMENT_DELIVERY_PENDING_MESSAGE,
            )

        order = await self.orders_service.update_order(
            order.id,
            status=OrderStatus.DELIVERY_FAILED.value,
            delivery_status=FragmentDeliveryStatus.FAILED.value,
            fragment_transaction_id=delivery_result.transaction_id,
        ) or order
        return PaymentDeliveryResult(
            order=order,
            payment_status=payment_status,
            delivery_status=FragmentDeliveryStatus.FAILED.value,
            user_message=self._get_delivery_failed_message(delivery_result),
        )

    def _get_payment_provider(self, provider_name: str | None):
        if provider_name == self.crypto_payment_provider.provider_name:
            return self.crypto_payment_provider

        return self.payment_provider

    @staticmethod
    def _get_delivery_failed_message(delivery_result) -> str:
        error_message = str(delivery_result.raw.get("error_message", "")).lower()
        if "buy button is disabled" in error_message:
            return FRAGMENT_DISABLED_BUY_MESSAGE

        return FRAGMENT_DELIVERY_FAILED_MESSAGE


async def create_stars_checkout(
    session: AsyncSession,
    *,
    user_id: int,
    recipient: str,
    recipient_tg_id: int,
    amount: int,
) -> StarsCheckoutResult:
    service = CheckoutService(session)
    return await service.create_stars_checkout(
        user_id=user_id,
        recipient=recipient,
        recipient_tg_id=recipient_tg_id,
        amount=amount,
    )


async def create_gift_checkout(
    session: AsyncSession,
    *,
    user_id: int,
    recipient: str,
    recipient_tg_id: int,
    gift_id: str,
    price_rub: Decimal,
) -> StarsCheckoutResult:
    service = CheckoutService(session)
    return await service.create_gift_checkout(
        user_id=user_id,
        recipient=recipient,
        recipient_tg_id=recipient_tg_id,
        gift_id=gift_id,
        price_rub=price_rub,
    )


async def confirm_payment_and_deliver(
    session: AsyncSession,
    *,
    order_id: int,
) -> PaymentDeliveryResult:
    service = CheckoutService(session)
    return await service.confirm_payment_and_deliver(order_id=order_id)


async def retry_delivery(
    session: AsyncSession,
    *,
    order_id: int,
) -> PaymentDeliveryResult:
    service = CheckoutService(session)
    return await service.retry_delivery(order_id=order_id)
