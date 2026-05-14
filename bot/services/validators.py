import re

# Telegram username: 5–32 символов, латиница, цифры, _
_USERNAME_RE = re.compile(r"^@?([a-zA-Z0-9_]{5,32})$")


def normalize_username(text: str) -> str | None:
    """Вернуть @username или None, если формат неверный."""
    if not text:
        return None
    raw = text.strip()
    m = _USERNAME_RE.match(raw)
    if not m:
        return None
    return f"@{m.group(1)}"


def parse_stars_amount(text: str) -> int | None:
    """Целое количество звёзд в допустимом диапазоне."""
    if not text:
        return None
    raw = text.strip().replace(" ", "")
    if not raw.isdigit():
        return None
    n = int(raw)
    if n < 1 or n > 1_000_000:
        return None
    return n
