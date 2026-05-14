# Заголовок для Phase 3-6
# Работа с БД (пользователи, ордеры, рефералы)

class Database:
    """Абстрактный слой для работы с БД"""

    async def add_user(self, user_id: int, username: str, language: str = "ru"):
        """Добавить пользователя"""
        pass

    async def get_user(self, user_id: int):
        """Получить пользователя"""
        pass
