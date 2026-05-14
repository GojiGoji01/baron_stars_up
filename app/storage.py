import logging

from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings


logger = logging.getLogger(__name__)


def create_fsm_storage() -> BaseStorage:
    if settings.fsm_storage == "redis":
        try:
            from aiogram.fsm.storage.redis import RedisStorage
        except ImportError:
            logger.warning("RedisStorage is unavailable, falling back to MemoryStorage")
            return MemoryStorage()

        logger.info("Using RedisStorage for FSM")
        return RedisStorage.from_url(settings.redis_url)

    logger.info("Using MemoryStorage for FSM")
    return MemoryStorage()
