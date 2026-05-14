from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.keyboards.main_menu import build_main_menu_keyboard
from app.texts.common import START_TEXT
from config import settings


router = Router(name="start")


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer_photo(
        photo=settings.start_image_url,
        caption=START_TEXT,
        reply_markup=build_main_menu_keyboard(),
    )
