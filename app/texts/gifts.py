GIFT_PREVIEW_TEXT = (
    "Покупка подарка\n\n"
    "Кому отправляем подарок?"
)


def gift_unknown_recipient_text() -> str:
    return "Покупка подарка\n\nПолучатель: не указан\n\nВведите username получателя вручную."


def gift_enter_recipient_text() -> str:
    return "Покупка подарка\n\nВведите username получателя.\n\nПример: @username"


def gift_list_text(recipient: str) -> str:
    return (
        "Покупка подарка\n\n"
        f"Получатель: {recipient}\n\n"
        "Выберите нужный подарок для покупки:\n"
        "Ниже показаны дешевые подарки для отправки с наценкой в рублях от 69 ₽."
    )


def gift_payment_text(recipient: str, amount: int) -> str:
    return (
        "Покупка подарка\n\n"
        f"Получатель: {recipient}\n"
        f"Стоимость: {amount} ₽\n\n"
        "Выберите способ оплаты."
    )
