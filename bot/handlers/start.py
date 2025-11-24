from typing import Optional

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

router = Router()


@router.message(Command("start"))
async def cmd_start(msg: Message):
    if msg.from_user is None:
        user_name = ""
    else:
        user_name = msg.from_user.first_name or ""
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Найти по названию", callback_data="search_by_name"
            )],
            [InlineKeyboardButton(
                text="Найти по предпочтениям", callback_data="search_by_preferences"
            )],
            [InlineKeyboardButton(
                text="Сообщить об ошибке", callback_data="report"
            )],
        ]
    )
    await msg.reply(
        text=f"Привет, {user_name}!👋 Я помогу подобрать фильм или сериал по твоим вкусам.",
        reply_markup=inline_kb
    )


async def show_main_menu(callback_or_message, state: Optional[FSMContext] = None):
    """Вспомогательная функция для отображения главного меню"""
    if state:
        await state.clear()

    if isinstance(callback_or_message, CallbackQuery):
        message = callback_or_message.message
        user = callback_or_message.from_user
    else:
        message = callback_or_message
        user = callback_or_message.from_user

    if not isinstance(message, Message) or user is None:
        return

    user_name = user.first_name or ""
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Найти по названию", callback_data="search_by_name"
            )],
            [InlineKeyboardButton(
                text="Найти по предпочтениям", callback_data="search_by_preferences"
            )],
            [InlineKeyboardButton(
                text="Сообщить об ошибке", callback_data="report"
            )],
        ]
    )

    text = f"Привет, {user_name}!👋 Я помогу подобрать фильм или сериал по твоим вкусам."

    if isinstance(callback_or_message, CallbackQuery):
        # Удаляем текущее сообщение и отправляем новое
        try:
            await message.delete()
        except Exception:
            pass
        if callback_or_message.bot:
            await callback_or_message.bot.send_message(
                chat_id=message.chat.id,
                text=text,
                reply_markup=inline_kb
            )
    else:
        await message.reply(text=text, reply_markup=inline_kb)


@router.callback_query(F.data.in_(["back_to_main", "cancel_search"]))
async def back_to_main_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик возврата в главное меню или отмены поиска"""
    await show_main_menu(callback, state)
    await callback.answer()
