from app.services.payments.base import PaymentInvoice


SBP_RECIPIENT_TG_ID_REQUIRED_TEXT = (
    "Для оплаты через СБП нужен Telegram ID получателя.\n\n"
    "Для покупки себе нажмите «СЕБЕ». Для покупки другу укажите Telegram ID получателя."
)


def payment_stars_text(recipient: str, amount: int) -> str:
    return (
        "Оформление заказа\n\n"
        "Продукт: Telegram Stars\n"
        f"👤 Получатель: {recipient}\n"
        f"⭐️ Количество: {amount}\n\n"
        "Выберите способ оплаты ниже."
    )


def payment_premium_text(recipient: str, premium_months: int) -> str:
    return (
        "Оформление заказа\n\n"
        "Продукт: Telegram Premium\n"
        f"⚜️ Срок: {premium_months} мес.\n"
        f"👤 Получатель: {recipient}\n\n"
        "Выберите способ оплаты ниже."
    )


def payment_gift_text(recipient: str, amount: int, gift_emoji: str | None = None) -> str:
    gift_line = f"🎁 Подарок: {gift_emoji}\n" if gift_emoji else ""
    return (
        "Оформление заказа\n\n"
        "Продукт: Telegram Gift\n"
        f"{gift_line}"
        f"👤 Получатель: {recipient}\n"
        f"💰 Стоимость: {amount} ₽\n\n"
        "Выберите способ оплаты ниже."
    )


def payment_invoice_text(order, invoice: PaymentInvoice) -> str:
    price = getattr(order, "price", None)
    if price is None:
        price = getattr(order, "price_rub", "")

    payment_method = getattr(order, "payment_method", None)
    if payment_method is None:
        payment_method = getattr(order, "payment_provider", "")

    return (
        "Оплата создана\n\n"
        f"Номер заказа: {order.order_id}\n"
        f"Тип заказа: {order.order_type}\n"
        f"Получатель: {order.recipient}\n"
        f"Количество: {order.amount}\n"
        f"Цена: {price} ₽\n"
        f"Способ оплаты: {str(payment_method).upper()}\n"
        f"Статус: {order.status}\n\n"
        f"Счет: {invoice.invoice_id}\n"
        f"Ссылка на оплату: {invoice.pay_url}"
    )


def sbp_invoice_created_text(order, invoice: PaymentInvoice) -> str:
    return (
        "✅ <b>Счёт создан успешно</b>\n\n"
        "🏦 <b>Способ оплаты:</b> СБП\n"
        f"💰 <b>Сумма к оплате:</b> <code>{invoice.amount} ₽</code>\n"
        f"🧾 <b>Transaction ID:</b> <code>{invoice.transaction_id}</code>\n"
        f"📦 <b>Заказ:</b> <code>{order.order_id}</code>\n\n"
        "ℹ️ <b>Инструкция:</b>\n"
        "1. Нажмите кнопку <b>💳 Оплатить</b> ниже.\n"
        "2. Подтвердите открытие ссылки внутри Telegram.\n"
        "3. Оплатите счёт на странице Platega.\n\n"
        "После оплаты статус будет проверен автоматически."
    )


def premium_sbp_invoice_created_text(order, invoice: PaymentInvoice) -> str:
    return (
        "✅ <b>Счёт Premium создан успешно</b>\n\n"
        "⚜️ <b>Продукт:</b> Telegram Premium\n"
        f"📅 <b>Срок:</b> <code>{order.amount} мес.</code>\n"
        f"👤 <b>Получатель:</b> <code>{order.recipient}</code>\n"
        "🏦 <b>Способ оплаты:</b> СБП\n\n"
        f"💰 <b>Сумма к оплате:</b> <code>{invoice.amount} ₽</code>\n"
        f"🧾 <b>Transaction ID:</b> <code>{invoice.transaction_id}</code>\n"
        f"📦 <b>Заказ:</b> <code>{order.order_id}</code>\n\n"
        "ℹ️ <b>Инструкция:</b>\n"
        "1. Нажмите кнопку <b>💳 Оплатить</b> ниже.\n"
        "2. Подтвердите открытие ссылки внутри Telegram.\n"
        "3. Оплатите счёт на странице Platega.\n\n"
        "После оплаты Premium будет обработан по статусу платежа."
    )


def gift_sbp_invoice_created_text(
    order,
    invoice: PaymentInvoice,
    gift_title: str | None = None,
) -> str:
    gift_line = f"🎁 <b>Подарок:</b> <code>{gift_title}</code>\n" if gift_title else ""
    gift_id_line = f"🆔 <b>Gift ID:</b> <code>{order.gift_id}</code>\n" if order.gift_id else ""
    return (
        "✅ <b>Счёт на подарок создан успешно</b>\n\n"
        "🎁 <b>Продукт:</b> Telegram Gift\n"
        f"{gift_line}"
        f"{gift_id_line}"
        f"👤 <b>Получатель:</b> <code>{order.recipient}</code>\n"
        "🏦 <b>Способ оплаты:</b> СБП\n\n"
        f"💰 <b>Сумма к оплате:</b> <code>{invoice.amount} ₽</code>\n"
        f"🧾 <b>Transaction ID:</b> <code>{invoice.transaction_id}</code>\n"
        f"📦 <b>Заказ:</b> <code>{order.order_id}</code>\n\n"
        "ℹ️ <b>Инструкция:</b>\n"
        "1. Нажмите кнопку <b>💳 Оплатить</b> ниже.\n"
        "2. Подтвердите открытие ссылки внутри Telegram.\n"
        "3. Оплатите счёт на странице Platega.\n\n"
        "После оплаты подарок будет отправлен автоматически."
    )
