from decimal import Decimal

from config import settings


def _format_money(value: Decimal | int | float) -> str:
    return f"{Decimal(str(value)).quantize(Decimal('0.01'))} ₽"


def _referral_details_text() -> str:
    return (
        "Подробности программы:\n"
        f"Приглашайте друзей и получайте {settings.referral_percent}% "
        "от нашей прибыли с ваших прямых рефералов."
    )


def build_referrals_text(
    referral_link: str,
    *,
    referral_count: int,
    active_referral_count: int,
    without_purchase_count: int,
    referral_balance: Decimal,
    total_referral_earned: Decimal,
) -> str:
    return (
        "Реферальная система\n\n"
        "Ваша статистика:\n"
        f"Рефералов: {referral_count}\n"
        f"Активные: {active_referral_count}\n"
        f"Без покупок: {without_purchase_count}\n"
        f"Реферальный баланс: {_format_money(referral_balance)}\n"
        f"Всего заработано: {_format_money(total_referral_earned)}\n\n"
        "Ваша реферальная ссылка:\n"
        f"{referral_link}\n\n"
        f"{_referral_details_text()}"
    )


def build_referrals_list_text(
    referral_items: list[tuple[int, str | None, Decimal, bool]] | tuple[tuple[int, str | None, Decimal, bool], ...],
    *,
    current_page: int,
    total_pages: int,
    total_items: int,
) -> str:
    if not referral_items:
        return "Мои рефералы\n\nУ вас пока нет приглашённых пользователей."

    lines = [
        "Мои рефералы",
        "",
        f"Всего: {total_items}",
        f"Страница: {current_page}/{total_pages}",
        "",
    ]

    for index, (_telegram_id, username, earned_amount, is_active) in enumerate(referral_items, start=1):
        name = f"@{username}" if username else "без username"
        status = "активный" if is_active else "без покупок"
        lines.append(f"{index}. {name} — {_format_money(earned_amount)} ({status})")

    return "\n".join(lines)


REFERRAL_WITHDRAW_ALERT = "Вывод реферального баланса будет добавлен позже."
