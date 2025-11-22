from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command


router = Router()


@router.message(Command("search_by_preferences"))
async def cmd_start(msg: Message):
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎥 Хочу фильм", callback_data="want_movie"), 
                InlineKeyboardButton(text="📺 Хочу сериал", callback_data="want_series")
            ],
            [
                InlineKeyboardButton(text="🤷 Пока не знаю", callback_data="dont_know")
            ]
        ]
    )
    await msg.reply(
        text="Ответь на пару вопросов — и я найду тебе то, что стоит посмотреть 🎬✨",
        reply_markup=inline_kb
    )