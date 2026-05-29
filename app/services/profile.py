from app.db.session import session_scope
from app.repositories.users import UsersRepository


async def get_profile_stats(user_id: int) -> dict:
    referral_balance = 0

    async with session_scope() as session:
        user = await UsersRepository(session).get_user_by_telegram_id(user_id)
        if user is not None:
            referral_balance = float(user.referral_balance)

    return {
        "user_id": user_id,
        "referral_balance": referral_balance,
        "stars_bought": 0,
        "stars_bought_rub": 0,
        "premium_months_bought": 0,
        "premium_bought_rub": 0,
        "total_deposit": 0,
        "saved_stars": 0,
        "saved_stars_rub": 0,
    }
