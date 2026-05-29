import logging
from dataclasses import dataclass

from app.services.antifraud.blacklist import (
    BLACKLISTED_RECIPIENTS,
    EXTRA_BLACKLISTED_TG_IDS,
)


logger = logging.getLogger(__name__)

ANTIFRAUD_BLOCKED_MESSAGE = "❌ Оплата недоступна для этого получателя. Пожалуйста, выберите другого получателя."


@dataclass(frozen=True)
class AntifraudResult:
    is_allowed: bool
    safe_message: str | None = None
    reason: str | None = None


def normalize_username(username: str | None) -> str | None:
    if username is None:
        return None

    normalized = username.strip().lower()
    if normalized.startswith("https://t.me/"):
        normalized = normalized.removeprefix("https://t.me/")
    if normalized.startswith("http://t.me/"):
        normalized = normalized.removeprefix("http://t.me/")
    if normalized.startswith("t.me/"):
        normalized = normalized.removeprefix("t.me/")
    normalized = normalized.lstrip("@").strip()
    return normalized or None


class AntifraudService:
    def __init__(self) -> None:
        self.blacklisted_usernames = {
            normalized
            for username, _ in BLACKLISTED_RECIPIENTS
            if (normalized := normalize_username(username)) is not None
        }
        self.blacklisted_tg_ids = {
            int(tg_id) for _, tg_id in BLACKLISTED_RECIPIENTS
        } | {int(tg_id) for tg_id in EXTRA_BLACKLISTED_TG_IDS}

    async def check_recipient(
        self,
        *,
        recipient: str | None,
        recipient_tg_id: int | str | None,
        user_id: int | None = None,
    ) -> AntifraudResult:
        normalized_username = normalize_username(recipient)
        normalized_tg_id = self._normalize_tg_id(recipient_tg_id)

        if normalized_tg_id is not None and normalized_tg_id in self.blacklisted_tg_ids:
            self._log_blocked_attempt(user_id, normalized_username, normalized_tg_id, "tg_id")
            return AntifraudResult(
                is_allowed=False,
                safe_message=ANTIFRAUD_BLOCKED_MESSAGE,
                reason="blacklisted_tg_id",
            )

        if normalized_username is not None and normalized_username in self.blacklisted_usernames:
            self._log_blocked_attempt(user_id, normalized_username, normalized_tg_id, "username")
            return AntifraudResult(
                is_allowed=False,
                safe_message=ANTIFRAUD_BLOCKED_MESSAGE,
                reason="blacklisted_username",
            )

        return AntifraudResult(is_allowed=True)

    @staticmethod
    def _normalize_tg_id(recipient_tg_id: int | str | None) -> int | None:
        if recipient_tg_id is None or recipient_tg_id == "":
            return None

        try:
            return int(recipient_tg_id)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _log_blocked_attempt(
        user_id: int | None,
        normalized_username: str | None,
        normalized_tg_id: int | None,
        reason: str,
    ) -> None:
        logger.warning(
            "antifraud_blocked_attempt user_id=%s recipient_username=%s recipient_tg_id=%s reason=%s",
            user_id,
            normalized_username,
            normalized_tg_id,
            reason,
        )
