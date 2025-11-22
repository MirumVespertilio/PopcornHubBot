from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command


router = Router()


@router.message(Command("search_by_name"))
async def cmd_start(msg: Message):
    await msg.reply(
        text="Напиши часть или название фильма/сериала и я помогу найти его🎬✨"
    )
