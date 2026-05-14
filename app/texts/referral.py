REFERRALS_DETAILS_TEXT = (
    "Подробности программы:\n"
    "Приглашайте друзей и получайте 70% от нашей прибыли с ваших прямых рефералов."
)


def build_referrals_text(referral_link: str) -> str:
    return (
        "Реферальная система\n\n"
        "Ваша статистика:\n\n"
        "Ваша реферальная ссылка:\n"
        f"{referral_link}\n\n"
        f"{REFERRALS_DETAILS_TEXT}"
    )


REFERRAL_WITHDRAW_ALERT = "Вывод реферального баланса будет добавлен позже."
REFERRAL_LIST_ALERT = "Список рефералов будет добавлен позже."
