import logging
import time
from dataclasses import dataclass
from typing import Any

import httpx

from config import settings


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GiftItem:
    gift_id: str
    emoji: str
    title: str
    price: int
    raw: dict[str, Any]

    @property
    def display_title(self) -> str:
        if not self.emoji:
            return self.title
        if self.title.startswith(self.emoji):
            return self.title
        return f"{self.emoji} {self.title}"


@dataclass
class GiftsCache:
    gifts: tuple[GiftItem, ...] = ()
    expires_at: float = 0.0


_gifts_cache = GiftsCache()


async def get_available_gifts(*, force_refresh: bool = False) -> tuple[GiftItem, ...]:
    now = time.monotonic()
    if not force_refresh and _gifts_cache.gifts and _gifts_cache.expires_at > now:
        return _gifts_cache.gifts

    gifts = await _load_telegram_gifts()
    _gifts_cache.gifts = gifts
    _gifts_cache.expires_at = now + settings.telegram_gifts_cache_seconds
    return gifts


async def get_gift_item(gift_id: int | str, *, force_refresh: bool = False) -> GiftItem:
    normalized_id = str(gift_id)
    gifts = await get_available_gifts(force_refresh=force_refresh)
    for gift in gifts:
        if gift.gift_id == normalized_id:
            return gift
    raise ValueError(f"Gift not found: {gift_id}")


async def get_gift_price(gift_id: int | str, *, force_refresh: bool = False) -> int:
    gift = await get_gift_item(gift_id, force_refresh=force_refresh)
    return gift.price


async def _load_telegram_gifts() -> tuple[GiftItem, ...]:
    token = settings.bot_token
    base_url = settings.telegram_api_base_url.rstrip("/")
    if not token:
        logger.error("telegram_gifts_bot_token_missing")
        return ()

    url = f"{base_url}/bot{token}/getAvailableGifts"
    try:
        async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
    except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.TransportError) as error:
        logger.warning(
            "telegram_gifts_load_failed error_type=%s",
            type(error).__name__,
        )
        return ()

    try:
        payload = response.json()
    except ValueError:
        logger.error("telegram_gifts_invalid_json")
        return ()

    if not payload.get("ok", False):
        logger.warning("telegram_gifts_api_not_ok")
        return ()

    raw_items = _extract_gift_items(payload.get("result"))
    gifts = tuple(item for item in (_normalize_gift(raw) for raw in raw_items) if item is not None)
    logger.info("telegram_gifts_loaded count=%s", len(gifts))
    return gifts


def _extract_gift_items(result: Any) -> list[dict[str, Any]]:
    if isinstance(result, list):
        return [item for item in result if isinstance(item, dict)]
    if isinstance(result, dict):
        gifts = result.get("gifts")
        if isinstance(gifts, list):
            return [item for item in gifts if isinstance(item, dict)]
    return []


def _normalize_gift(item: dict[str, Any]) -> GiftItem | None:
    gift_id = _first_value(item, "id", "gift_id")
    if gift_id is None:
        return None

    emoji = _extract_gift_emoji(item)
    title = str(_first_value(item, "title", "name", "label") or f"Gift {gift_id}")
    price = _first_value(item, "star_count", "amount", "price")
    if price is None:
        price = 0

    try:
        return GiftItem(
            gift_id=str(gift_id),
            emoji=emoji,
            title=title,
            price=int(price),
            raw=item,
        )
    except (TypeError, ValueError):
        return None


def _extract_gift_emoji(item: dict[str, Any]) -> str:
    direct_emoji = _first_value(item, "emoji")
    if isinstance(direct_emoji, str) and direct_emoji.strip():
        return direct_emoji.strip()

    sticker = item.get("sticker")
    if isinstance(sticker, dict):
        sticker_emoji = sticker.get("emoji")
        if isinstance(sticker_emoji, str) and sticker_emoji.strip():
            return sticker_emoji.strip()

    title = _first_value(item, "title", "name", "label")
    if isinstance(title, str) and title.strip():
        first_token = title.strip().split(maxsplit=1)[0]
        if any(ord(char) > 127 for char in first_token):
            return first_token

    return "🎁"


def _first_value(item: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = item.get(key)
        if value is not None:
            return value
    return None
