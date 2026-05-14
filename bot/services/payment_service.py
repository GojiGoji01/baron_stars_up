# Заголовок для Phase 4
# Система обработки платежей (TON, SBP, Crypto)

class PaymentService:
    """Абстрактный слой для платежных систем"""

    async def create_order(self, user_id: int, amount: float, currency: str):
        """Создать ордер"""
        pass

    async def check_payment(self, order_id: str):
        """Проверить статус платежа"""
        pass
