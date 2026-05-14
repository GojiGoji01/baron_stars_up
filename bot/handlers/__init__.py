from aiogram import Router

from .buy import router as buy_router
from .menu import router as menu_router
from .start import router as start_router

router = Router()
router.include_router(start_router)
router.include_router(buy_router)
router.include_router(menu_router)

__all__ = ["router"]
