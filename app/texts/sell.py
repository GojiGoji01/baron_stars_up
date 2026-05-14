SELL_STARS_TEXT = (
    "Продажа Звезд\n\n"
    "Курс выкупа: 0.80 ₽ за 1 ⭐️\n\n"
    "Минимум: 50 звезд\n"
    "Максимум за один заказ: 100 000 звезд\n\n"
    "Введите количество звезд для продажи:"
)


def sell_stars_summary_text(amount: int, payout: float) -> str:
    return (
        "Продажа Звезд\n\n"
        f"⭐️ Количество: {amount}\n"
        "Курс выкупа: 0.80 ₽ за 1 ⭐️\n"
        f"К выплате: {payout:.2f} ₽\n\n"
        "Заявка будет оформлена после подключения системы выплат."
    )


SELL_STARS_NUMBER_REQUIRED_TEXT = "Введите количество звезд числом."


def sell_stars_range_text(min_amount: int, max_amount: int) -> str:
    return f"Количество должно быть от {min_amount} до {max_amount} звезд."
