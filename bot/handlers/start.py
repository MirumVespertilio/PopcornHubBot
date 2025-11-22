from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command

router = Router()


@router.message(Command("start"))
async def cmd_start(msg: Message):
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Найти по названию", callback_data="search_by_name")],
            [InlineKeyboardButton(text="Найти по предпочтениям", callback_data="search_by_preferences")],
            [InlineKeyboardButton(text="Сообщить об ошибке", callback_data="report")],
        ]
    )
    await msg.reply(
        text="Привет! 👋 Я помогу подобрать фильм или сериал по твоим вкусам.",
        reply_markup=inline_kb
    )


# # добавляем обработчик callback'ов — после нажатия убираем клавиатуру
# @router.callback_query()
# async def handle_choice(callback: CallbackQuery):
#     data = callback.data
#     # убираем inline-кнопки у сообщения
#     await callback.message.edit_reply_markup(reply_markup=None)
#     # отвечаем пользователю и закрываем "часики" на кнопке
#     if data == "want_movie":
#         await callback.message.answer("Отлично — ищу фильм...")
#     elif data == "want_series":
#         await callback.message.answer("Отлично — ищу сериал...")
#     else:
#         await callback.message.answer("Хорошо, дам пару вариантов.")
#     await callback.answer()