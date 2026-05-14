from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import settings


router = Router(name="admin")


def _is_admin(user_id: int) -> bool:
    return user_id in settings.admin_owner_ids or user_id in settings.admin_manager_ids


@router.message(Command("admin"))
async def handle_admin(message: Message) -> None:
    if message.from_user is None or not _is_admin(message.from_user.id):
        await message.answer("Доступ запрещен.")
        return

    await message.answer(
        "Admin area\n\n"
        "Ручная выдача Stars через менеджера будет подключена здесь.\n"
        "Referral начисления должны выполняться только после completed orders."
    )
