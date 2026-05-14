from .ru import RU
from .en import EN

LOCALES = {
    "ru": RU,
    "en": EN,
}

def get_text(lang: str, key: str, default: str = "") -> str:
    """Получить текст по языку и ключу"""
    return LOCALES.get(lang, RU).get(key, default)
