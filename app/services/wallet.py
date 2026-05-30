from dataclasses import dataclass
import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.users import UsersRepository


class WalletBindingError(Exception):
    pass


@dataclass(frozen=True)
class WalletBindingResult:
    telegram_id: int
    wallet_address: str
    wallet_provider: str
    wallet_status: str


TON_ADDRESS_RE = re.compile(r"^(EQ|UQ|kQ|0Q)[A-Za-z0-9_-]{46,64}$")


def is_valid_ton_wallet_address(value: str) -> bool:
    address = value.strip()
    if not address:
        return False
    if TON_ADDRESS_RE.match(address):
        return True
    # raw TON address fallback: workchain:hex
    if ":" in address:
        workchain, _, hex_part = address.partition(":")
        if workchain in {"-1", "0"} and len(hex_part) == 64:
            return all(char in "0123456789abcdefABCDEF" for char in hex_part)
    return False


class WalletService:
    def __init__(self, session: AsyncSession) -> None:
        self.users = UsersRepository(session)

    async def connect_wallet(
        self,
        *,
        telegram_id: int,
        wallet_address: str,
        wallet_provider: str = "tonkeeper",
    ) -> WalletBindingResult:
        if not is_valid_ton_wallet_address(wallet_address):
            raise WalletBindingError("invalid wallet address")
        try:
            user = await self.users.bind_wallet(
                telegram_id=telegram_id,
                wallet_address=wallet_address,
                wallet_provider=wallet_provider,
            )
        except ValueError as error:
            raise WalletBindingError(str(error)) from error

        if user is None:
            raise WalletBindingError("user not found")

        return WalletBindingResult(
            telegram_id=user.telegram_id,
            wallet_address=user.wallet_address or "",
            wallet_provider=user.wallet_provider or wallet_provider,
            wallet_status=user.wallet_status or "connected",
        )

    async def disconnect_wallet(self, *, telegram_id: int) -> None:
        user = await self.users.disconnect_wallet(telegram_id=telegram_id)
        if user is None:
            raise WalletBindingError("user not found")

    async def verify_wallet(self, *, telegram_id: int) -> WalletBindingResult:
        user = await self.users.touch_wallet_verified_at(telegram_id=telegram_id)
        if user is None:
            raise WalletBindingError("user not found")
        if not user.wallet_address:
            raise WalletBindingError("wallet not connected")

        return WalletBindingResult(
            telegram_id=user.telegram_id,
            wallet_address=user.wallet_address,
            wallet_provider=user.wallet_provider or "tonkeeper",
            wallet_status=user.wallet_status or "connected",
        )
