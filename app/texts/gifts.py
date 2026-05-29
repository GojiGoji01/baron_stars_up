GIFT_PREVIEW_TEXT = (
    "Покупка подарка\n\n"
    "Кому отправляем подарок?"
)

GIFTS_UNAVAILABLE_TEXT = (
    "Покупка подарка\n\n"
    "Список подарков временно недоступен. Попробуйте позже."
)


def gift_unknown_recipient_text() -> str:
    return (
        "Покупка подарка\n\n"
        "Получатель: не указан\n\n"
        "Введите username получателя вручную."
    )


def gift_enter_recipient_text() -> str:
    return "Покупка подарка\n\nВведите username получателя.\n\nПример: @username"


def gift_enter_recipient_tg_id_text(recipient: str) -> str:
    return (
        "Покупка подарка\n\n"
        f"Получатель: {recipient}\n\n"
        "Введите Telegram ID получателя для оплаты через СБП.\n"
        "Пример: 123456789"
    )


def gift_recipient_tg_id_invalid_text() -> str:
    return "Telegram ID должен быть числом. Пример: 123456789"


def gift_list_text(recipient: str) -> str:
    return (
        "Покупка подарка\n\n"
        f"Получатель: {recipient}\n\n"
        "Выберите нужный подарок для покупки:"
    )


def gift_payment_text(recipient: str, amount: int, gift_emoji: str | None = None) -> str:
    gift_line = f"Подарок: {gift_emoji}\n" if gift_emoji else ""
    return (
        "Покупка подарка\n\n"
        f"Получатель: {recipient}\n"
        f"{gift_line}"
        f"Стоимость: {amount} ₽\n\n"
        "Выберите способ оплаты."
    )
