import logging
import time
from dataclasses import dataclass
from typing import Any

import httpx

from config import settings


logger = logging.getLogger(__name__)

BYBIT_P2P_ONLINE_URL = "https://api2.bybit.com/fiat/otc/item/online"


@dataclass
class ExchangeRateCache:
    rate: float | None = None
    expires_at: float = 0.0


_exchange_rate_cache = ExchangeRateCache()


async def get_usdt_rub_rate() -> float:
    now = time.monotonic()
    if _exchange_rate_cache.rate is not None and _exchange_rate_cache.expires_at > now:
        return _exchange_rate_cache.rate

    if settings.exchange_rate_provider in {"bybit", "bybit_p2p"}:
        rate = await _get_bybit_p2p_usdt_rub_rate()
    else:
        rate = settings.default_usd_rub_rate

    rate_with_spread = rate * (1 + settings.exchange_rate_spread_percent / 100)
    final_rate = round(rate_with_spread, 4)

    _exchange_rate_cache.rate = final_rate
    _exchange_rate_cache.expires_at = now + settings.exchange_rate_cache_seconds

    logger.info(
        "exchange_rate_loaded provider=%s base_rate=%s spread_percent=%s final_rate=%s",
        settings.exchange_rate_provider,
        rate,
        settings.exchange_rate_spread_percent,
        final_rate,
    )
    return final_rate


async def _get_bybit_p2p_usdt_rub_rate() -> float:
    payload = {
        "userId": "",
        "tokenId": "USDT",
        "currencyId": "RUB",
        "payment": [],
        "side": "1",
        "size": "10",
        "page": "1",
        "amount": settings.bybit_p2p_amount,
    }

    try:
        async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
            response = await client.post(BYBIT_P2P_ONLINE_URL, json=payload)
            response.raise_for_status()
    except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.TransportError) as error:
        logger.warning(
            "bybit_p2p_exchange_rate_failed fallback_rate=%s error_type=%s",
            settings.default_usd_rub_rate,
            type(error).__name__,
        )
        return settings.default_usd_rub_rate

    try:
        data = response.json()
    except ValueError:
        logger.error(
            "bybit_p2p_exchange_rate_invalid_json fallback_rate=%s",
            settings.default_usd_rub_rate,
        )
        return settings.default_usd_rub_rate

    items = _extract_bybit_items(data)
    prices = []
    for item in items[:5]:
        try:
            prices.append(float(item["price"]))
        except (KeyError, TypeError, ValueError):
            continue

    if not prices:
        logger.error(
            "bybit_p2p_exchange_rate_invalid_response fallback_rate=%s response_keys=%s",
            settings.default_usd_rub_rate,
            sorted(data.keys()),
        )
        return settings.default_usd_rub_rate

    average_rate = round(sum(prices) / len(prices), 4)
    logger.info(
        "bybit_p2p_exchange_rate_loaded top_count=%s average_rate=%s amount=%s",
        len(prices),
        average_rate,
        settings.bybit_p2p_amount,
    )
    return average_rate


def _extract_bybit_items(data: dict[str, Any]) -> list[dict[str, Any]]:
    result = data.get("result")
    if not isinstance(result, dict):
        return []

    items = result.get("items")
    if isinstance(items, list):
        return [item for item in items if isinstance(item, dict)]

    return []
