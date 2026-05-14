async def get_profile_stats(user_id: int) -> dict:
    return {
        "user_id": user_id,
        "referral_balance": 0,
        "stars_bought": 0,
        "stars_bought_rub": 0,
        "premium_months_bought": 0,
        "premium_bought_rub": 0,
        "total_deposit": 0,
        "saved_stars": 0,
        "saved_stars_rub": 0,
    }
