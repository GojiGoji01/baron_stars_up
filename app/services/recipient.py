import re


USERNAME_PATTERN = re.compile(r"^@?[A-Za-z0-9_]{5,32}$")


async def validate_username(value: str) -> bool:
    return USERNAME_PATTERN.fullmatch(value.strip()) is not None


async def normalize_username(value: str) -> str | None:
    username = value.strip()

    if not await validate_username(username):
        return None

    return username if username.startswith("@") else f"@{username}"
