from aiogram import Router
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import FSInputFile, Message

from app.db.session import session_scope
from app.keyboards.main_menu import build_main_menu_keyboard
from app.services.referral import register_referral_start
from app.texts.common import START_TEXT
from config import settings


router = Router(name="start")


def _get_start_photo() -> str | FSInputFile:
    if settings.start_image_url.startswith(("http://", "https://")):
        return settings.start_image_url

    return FSInputFile(settings.start_image_url)


@router.message(CommandStart())
async def handle_start(message: Message, command: CommandObject) -> None:
    if message.from_user is not None:
        async with session_scope() as session:
            await register_referral_start(
                session,
                user_id=message.from_user.id,
                username=message.from_user.username,
                payload=command.args,
            )

    await message.answer_photo(
        photo=_get_start_photo(),
        caption=START_TEXT,
        reply_markup=build_main_menu_keyboard(),
    )
