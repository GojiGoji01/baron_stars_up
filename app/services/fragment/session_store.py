from __future__ import annotations

from typing import Any

from sqlalchemy import select

from app.db.models.fragment_browser_session import FragmentBrowserSession
from app.db.session import session_scope


class FragmentSessionStore:
    async def load_state(self) -> dict[str, Any] | None:
        async with session_scope() as session:
            result = await session.execute(
                select(FragmentBrowserSession).where(FragmentBrowserSession.source == "fragment")
            )
            row = result.scalar_one_or_none()
            if row is None:
                return None
            return {
                "cookies_base64": row.cookies_base64,
                "local_storage_base64": row.local_storage_base64,
                "updated_at": row.updated_at,
            }

    async def save_state(self, *, cookies_base64: str, local_storage_base64: str) -> None:
        async with session_scope() as session:
            result = await session.execute(
                select(FragmentBrowserSession).where(FragmentBrowserSession.source == "fragment")
            )
            row = result.scalar_one_or_none()
            if row is None:
                session.add(
                    FragmentBrowserSession(
                        source="fragment",
                        cookies_base64=cookies_base64,
                        local_storage_base64=local_storage_base64,
                    )
                )
                return

            row.cookies_base64 = cookies_base64
            row.local_storage_base64 = local_storage_base64
