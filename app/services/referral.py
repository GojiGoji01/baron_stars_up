import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.users import UsersRepository
from config import settings


logger = logging.getLogger(__name__)

REFERRAL_LINK_BOT_USERNAME = "baron_stars_bot"


@dataclass(frozen=True)
class ReferralBindResult:
    user_id: int
    referred_by: int | None = None
    status: str = "skipped"


async def generate_referral_link(user_id: int) -> str:
    return f"https://t.me/{REFERRAL_LINK_BOT_USERNAME}?start={user_id}"


def parse_referral_payload(payload: str | None) -> int | None:
    if not payload:
        return None

    normalized_payload = payload.strip()
    if not normalized_payload:
        return None

    logger.info("referral_start_payload_received payload=%s", normalized_payload)

    if normalized_payload.isdigit():
        return int(normalized_payload)

    if normalized_payload.startswith("ref_"):
        referrer_id = normalized_payload.removeprefix("ref_").strip()
        if referrer_id.isdigit():
            return int(referrer_id)

    return None


async def register_referral_start(
    session: AsyncSession,
    *,
    user_id: int,
    username: str | None,
    payload: str | None,
) -> ReferralBindResult:
    users_repository = UsersRepository(session)
    user = await users_repository.get_or_create_user(
        telegram_id=user_id,
        username=username,
    )

    if not settings.referrals_enabled:
        return ReferralBindResult(user_id=user_id, referred_by=user.referred_by, status="disabled")

    referrer_id = parse_referral_payload(payload)
    if referrer_id is None:
        return ReferralBindResult(user_id=user_id, referred_by=user.referred_by, status="no_payload")

    if referrer_id == user_id:
        logger.info("referral_skipped_self user_id=%s referrer_id=%s", user_id, referrer_id)
        return ReferralBindResult(user_id=user_id, referred_by=user.referred_by, status="self")

    if user.referred_by is not None:
        logger.info(
            "referral_skipped_existing user_id=%s existing_referred_by=%s incoming_referrer_id=%s",
            user_id,
            user.referred_by,
            referrer_id,
        )
        return ReferralBindResult(user_id=user_id, referred_by=user.referred_by, status="existing")

    await users_repository.set_referred_by_once(user_id, referrer_id)
    logger.info("referral_saved user_id=%s referred_by=%s", user_id, referrer_id)
    return ReferralBindResult(user_id=user_id, referred_by=referrer_id, status="saved")
