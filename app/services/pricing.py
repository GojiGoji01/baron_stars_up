STARS_MIN_AMOUNT = 50
STARS_MAX_AMOUNT = 100000
SELL_STARS_MIN_AMOUNT = 50
SELL_STARS_MAX_AMOUNT = 100000
SELL_STARS_RATE_RUB = 0.8


async def calculate_star_price(amount: int) -> int:
    return amount


async def calculate_sell_price(amount: int) -> float:
    return amount * SELL_STARS_RATE_RUB


async def validate_stars_amount(amount: int) -> bool:
    return STARS_MIN_AMOUNT <= amount <= STARS_MAX_AMOUNT


async def validate_sell_stars_amount(amount: int) -> bool:
    return SELL_STARS_MIN_AMOUNT <= amount <= SELL_STARS_MAX_AMOUNT
