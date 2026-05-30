from __future__ import annotations

from typing import Any


CONNECT_CTA_MARKERS = (
    "Connect TON",
    "Connect wallet",
    "to view your bids and assets",
)


async def collect_fragment_page_state(page: Any) -> dict[str, Any]:
    local_storage_keys = await page.evaluate(
        """
        () => Array.from({ length: localStorage.length }, (_, i) => localStorage.key(i))
        """
    )
    session_storage_keys = await page.evaluate(
        """
        () => Array.from({ length: sessionStorage.length }, (_, i) => sessionStorage.key(i))
        """
    )
    body_text = await page.locator("body").inner_text()
    title = await page.title()

    body_text_lower = body_text.lower()
    connect_wallet_visible = await page.locator("text=Connect wallet").count() > 0
    connect_ton_visible = "connect ton" in body_text_lower
    connect_cta_visible = connect_wallet_visible or connect_ton_visible or (
        "to view your bids and assets" in body_text_lower
    )

    ton_connect_keys = [key for key in local_storage_keys if str(key).startswith("ton-connect")]
    wallet_session_ready = bool(ton_connect_keys) and not connect_cta_visible

    return {
        "fragment_url": page.url,
        "fragment_title": title,
        "fragment_connect_wallet_visible": connect_wallet_visible,
        "fragment_connect_ton_visible": connect_ton_visible,
        "fragment_connect_cta_visible": connect_cta_visible,
        "fragment_local_storage_key_count": len(local_storage_keys),
        "fragment_session_storage_key_count": len(session_storage_keys),
        "fragment_ton_connect_key_count": len(ton_connect_keys),
        "fragment_wallet_session_ready": wallet_session_ready,
        "fragment_body_excerpt": body_text[:600],
    }
