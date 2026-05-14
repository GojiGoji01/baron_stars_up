from app.services.orders import Order
from app.services.payments.base import BasePaymentProvider, PaymentInvoice, PaymentStatus


class TonPaymentProvider(BasePaymentProvider):
    payment_method = "ton"

    async def create_invoice(self, order: Order) -> PaymentInvoice:
        return PaymentInvoice(
            invoice_id=f"TON-{order.order_id}",
            order_id=order.order_id,
            payment_method=self.payment_method,
            amount=order.price,
            pay_url=f"https://pay.example.local/ton/{order.order_id}",
            status=PaymentStatus.PENDING.value,
        )

    async def check_payment(self, invoice_id: str) -> PaymentStatus:
        return PaymentStatus.PENDING

    async def cancel_invoice(self, invoice_id: str) -> PaymentStatus:
        return PaymentStatus.CANCELED
