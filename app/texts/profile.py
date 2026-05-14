def build_profile_text(stats: dict) -> str:
    return (
        "Ваш профиль\n\n"
        f"Ваш ID: {stats['user_id']}\n"
        f"Реферальный баланс: {stats['referral_balance']} ₽\n"
        f"Всего куплено звёзд: {stats['stars_bought']} ({stats['stars_bought_rub']} ₽)\n"
        f"Всего куплено премиумов (мес): {stats['premium_months_bought']} ({stats['premium_bought_rub']} ₽)\n"
        f"Общий депозит: {stats['total_deposit']} ₽\n"
        f"Накоплено звезд: {stats['saved_stars']} ({stats['saved_stars_rub']} ₽)"
    )


PROFILE_WITHDRAW_STARS_ALERT = "Вывод звезд будет добавлен позже."
