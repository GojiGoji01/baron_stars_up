import logging
import time
from dataclasses import dataclass

from app.services.exchange_rate import get_usdt_rub_rate
from app.services.fragment.client import FragmentAPIService
from config import settings


logger = logging.getLogger(__name__)

STARS_MIN_AMOUNT = settings.min_stars_amount
STARS_MAX_AMOUNT = settings.max_stars_amount
SELL_STARS_MIN_AMOUNT = 50
SELL_STARS_MAX_AMOUNT = 100000
SELL_STARS_RATE_RUB = 0.8
ORDER_TIMEOUT_MINUTES = settings.order_timeout_minutes
SERVICE_COMMISSION_PERCENT = settings.service_commission_percent
PLATEGA_COMMISSION_PERCENT = settings.platega_commission_percent
PLATEGA_DISPLAY_COMMISSION_PERCENT = settings.platega_display_commission_percent


@dataclass
class FragmentRatesCache:
    rates: dict[str, float] | None = None
    expires_at: float = 0.0


_fragment_rates_cache = FragmentRatesCache()


async def calculate_star_price(amount: int) -> float:
    fragment_price_usd = await _calculate_fragment_price_usd(amount)
    rate = await get_usdt_rub_rate()
    price_rub = fragment_price_usd * rate
    price_with_service_commission = price_rub * (1 + SERVICE_COMMISSION_PERCENT / 100)
    return round(price_with_service_commission, 2)


async def calculate_sbp_price(amount: int | float) -> float:
    price = float(amount) * (1 + PLATEGA_COMMISSION_PERCENT / 100)
    return round(price, 2)


async def calculate_platega_display_price(amount: int | float) -> float:
    price = float(amount) * (1 + PLATEGA_DISPLAY_COMMISSION_PERCENT / 100)
    return round(price, 2)


async def calculate_premium_price(months: int) -> float:
    prices = {
        3: settings.premium_price_3_months,
        6: settings.premium_price_6_months,
        12: settings.premium_price_12_months,
    }
    return round(float(prices.get(months, settings.premium_price_3_months)), 2)


async def calculate_sell_price(amount: int) -> float:
    return round(amount * SELL_STARS_RATE_RUB, 2)


async def validate_stars_amount(amount: int) -> bool:
    return STARS_MIN_AMOUNT <= amount <= STARS_MAX_AMOUNT


async def validate_sell_stars_amount(amount: int) -> bool:
    return SELL_STARS_MIN_AMOUNT <= amount <= SELL_STARS_MAX_AMOUNT


async def _calculate_fragment_price_usd(amount: int) -> float:
    try:
        rates = await get_fragment_rates()
        commission_decimal = _get_fragment_commission_decimal(rates)
        base_price_usd = amount * settings.fragment_star_base_usd
        return round(base_price_usd * (1 + commission_decimal), 4)
    except Exception as error:
        logger.exception(
            "fragment_price_calculation_failed amount=%s error_type=%s",
            amount,
            type(error).__name__,
        )
        if not settings.price_fallback_to_static_rate:
            raise

        return round(amount * settings.fragment_star_base_usd, 4)


async def get_fragment_rates() -> dict[str, float]:
    now = time.monotonic()
    if _fragment_rates_cache.rates is not None and _fragment_rates_cache.expires_at > now:
        return _fragment_rates_cache.rates

    service = FragmentAPIService(
        wallet_mnemonic=settings.fragment_wallet_mnemonic,
        api_url=settings.fragment_effective_api_url,
        api_mode=settings.fragment_api_mode,
        cookies_base64=settings.fragment_cookies_base64,
    )
    rates = await service.get_rates()
    _fragment_rates_cache.rates = rates
    _fragment_rates_cache.expires_at = now + settings.price_rates_cache_ttl_seconds

    logger.info(
        "fragment_rates_loaded mode=%s no_kyc_decimal=%s kyc_decimal=%s",
        settings.fragment_api_mode,
        rates.get("no_kyc_decimal"),
        rates.get("kyc_decimal"),
    )
    return rates


def _get_fragment_commission_decimal(rates: dict[str, float]) -> float:
    if settings.fragment_api_mode == "kyc":
        return float(rates.get("kyc_decimal", 0.0))

    return float(rates.get("no_kyc_decimal", 0.0))
