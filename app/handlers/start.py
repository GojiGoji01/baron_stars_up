from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile, Message

from app.keyboards.main_menu import build_main_menu_keyboard
from app.texts.common import START_TEXT
from config import settings


router = Router(name="start")


def _get_start_photo() -> str | FSInputFile:
    if settings.start_image_url.startswith(("http://", "https://")):
        return settings.start_image_url

    return FSInputFile(settings.start_image_url)


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer_photo(
        photo=_get_start_photo(),
        caption=START_TEXT,
        reply_markup=build_main_menu_keyboard(),
    )
