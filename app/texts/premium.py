def premium_start_text() -> str:
    return "Telegram Premium\n\nКому оформляем Premium?"


def premium_duration_text() -> str:
    return "Telegram Premium\n\nВыберите срок подписки."


def premium_target_text(premium_months: int) -> str:
    return (
        "Telegram Premium\n\n"
        f"⚜️ Срок: {premium_months} мес.\n\n"
        "Кому оформляем Premium?"
    )


def premium_self_already_active_alert() -> str:
    return "У вас уже есть Telegram Premium. Можно подарить Premium другу."


def premium_enter_recipient_text() -> str:
    return "Telegram Premium\n\nВведите username получателя.\n\nПример: @username"


def premium_enter_recipient_tg_id_text(recipient: str) -> str:
    return (
        "Telegram Premium\n\n"
        f"👤 Получатель: {recipient}\n\n"
        "Введите Telegram ID получателя для оплаты через SBP.\n"
        "Пример: 123456789"
    )


def premium_recipient_tg_id_invalid_text() -> str:
    return "Telegram ID должен быть числом. Пример: 123456789"


def premium_unknown_recipient_text(premium_months: int) -> str:
    return (
        "Telegram Premium\n\n"
        f"⚜️ Срок: {premium_months} мес.\n"
        "👤 Получатель: не указан\n\n"
        "Введите username получателя вручную."
    )


def premium_payment_text(premium_months: int, recipient: str) -> str:
    return (
        "Telegram Premium\n\n"
        f"⚜️ Срок: {premium_months} мес.\n"
        f"👤 Получатель: {recipient}\n\n"
        "Выберите способ оплаты."
    )
