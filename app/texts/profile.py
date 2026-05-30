def _wallet_line(stats: dict) -> str:
    wallet_address = stats.get("wallet_address")
    wallet_status = stats.get("wallet_status") or "not_connected"
    wallet_provider = stats.get("wallet_provider") or "-"

    if not wallet_address:
        return "Wallet: not connected"

    return f"Wallet: {wallet_address} ({wallet_provider}, {wallet_status})"


def build_profile_text(stats: dict) -> str:
    return (
        "Ваш профиль\n\n"
        f"Ваш ID: {stats['user_id']}\n"
        f"{_wallet_line(stats)}\n"
        f"Реферальный баланс: {stats['referral_balance']} ₽\n"
        f"Всего куплено звёзд: {stats['stars_bought']} ({stats['stars_bought_rub']} ₽)\n"
        f"Всего куплено премиумов (мес): {stats['premium_months_bought']} ({stats['premium_bought_rub']} ₽)\n"
        f"Общий депозит: {stats['total_deposit']} ₽\n"
        f"Накоплено звезд: {stats['saved_stars']} ({stats['saved_stars_rub']} ₽)"
    )


PROFILE_WITHDRAW_STARS_ALERT = "Вывод звезд будет добавлен позже."
PROFILE_CONNECT_WALLET_PROMPT = (
    "Отправьте TON-адрес кошелька Tonkeeper (формат EQ... или UQ...)."
)
PROFILE_CONNECT_WALLET_SUCCESS = "Кошелек успешно привязан."
PROFILE_CONNECT_WALLET_INVALID = "Некорректный TON-адрес. Проверьте формат и отправьте снова."
PROFILE_WALLET_DISCONNECTED = "Кошелек отключен."
PROFILE_WALLET_NOT_CONNECTED = "Кошелек не подключен."
PROFILE_WALLET_VERIFY_OK = "Кошелек активен, проверка сохранена."
