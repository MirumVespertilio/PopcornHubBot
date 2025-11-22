from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart

router = Router()


@router.message(CommandStart)
async def cmd_start(msg: Message):
    if msg.from_user is None:
        user_name = ""
    else:
        user_name = msg.from_user.first_name or ""
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Найти по названию", callback_data="search_by_name")],
            [InlineKeyboardButton(text="Найти по предпочтениям", callback_data="search_by_preferences")],
            [InlineKeyboardButton(text="Сообщить об ошибке", callback_data="report")],
        ]
    )
    await msg.reply(
        text=f"Привет, {user_name}!👋 Я помогу подобрать фильм или сериал по твоим вкусам.",
        reply_markup=inline_kb
    )



# @router.callback_query(F.data == "search_by_name")
# async def search_by_name_handler(callback: CallbackQuery):
#     await callback.answer()  # Убирает часы загрузки на кнопке
#     await callback.message.edit_text(
#         text="Введите название фильма или сериала:"
#     )
