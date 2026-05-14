from aiogram import Router

from app.handlers.buy import router as buy_router
from app.handlers.errors import router as errors_router
from app.handlers.menu import router as menu_router
from app.handlers.start import router as start_router
from app.routers.admin import router as admin_router


def setup_routers() -> Router:
    router = Router(name="root")
    router.include_router(start_router)
    router.include_router(admin_router)
    router.include_router(buy_router)
    router.include_router(menu_router)
    router.include_router(errors_router)
    return router
