TON_PREVIEW_TEXT = (
    "Покупка TON\n\n"
    "Выберите количество TON для покупки."
)


def ton_enter_amount_text() -> str:
    return "Покупка TON\n\nВведите количество TON для покупки."


def ton_payment_text(amount: int | float) -> str:
    return (
        "Покупка TON\n\n"
        f"💎 Количество: {amount:g} TON\n\n"
        "Выберите способ оплаты."
    )


TON_AMOUNT_NUMBER_REQUIRED_TEXT = "Введите количество TON числом."
TON_AMOUNT_POSITIVE_TEXT = "Количество TON должно быть больше нуля."
