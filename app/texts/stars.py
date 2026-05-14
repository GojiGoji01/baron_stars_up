def stars_recipient_choice_text() -> str:
    return "Telegram Stars\n\nКому покупаем звезды?"


def stars_enter_recipient_text() -> str:
    return "Telegram Stars\n\nВведите username получателя.\n\nПример: @username"


def stars_unknown_recipient_text() -> str:
    return "Telegram Stars\n\n👤 Получатель: не указан\n\nВведите username получателя вручную."


def stars_amount_text(recipient: str) -> str:
    return (
        "Telegram Stars\n\n"
        f"👤 Получатель: {recipient}\n\n"
        "Выберите количество звезд."
    )


def stars_custom_amount_text(recipient: str, min_amount: int, max_amount: int) -> str:
    return (
        "Telegram Stars\n\n"
        f"👤 Получатель: {recipient}\n\n"
        f"Введите количество звезд от {min_amount} до {max_amount}."
    )


def stars_payment_text(recipient: str, amount: int) -> str:
    return (
        "Telegram Stars\n\n"
        f"👤 Получатель: {recipient}\n"
        f"⭐️ Количество: {amount}\n\n"
        "Выберите способ оплаты."
    )


def stars_amount_number_required_text() -> str:
    return "Введите сумму числом."


def stars_amount_range_text(min_amount: int, max_amount: int) -> str:
    return f"Сумма должна быть от {min_amount} до {max_amount} звезд."
