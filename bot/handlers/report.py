from aiogram import Router, F
from aiogram.types import CallbackQuery, Message


router = Router()


@router.callback_query(F.data == "report")
async def report_handler(callback: CallbackQuery):
    if not callback.message or not isinstance(callback.message, Message):
        await callback.answer("Ошибка: Сообщение не найдено", show_alert=True)
        return

    # Store chat_id before deleting
    chat_id = callback.message.chat.id

    # Delete the welcome message
    await callback.message.delete()

    # Send new message using bot instance
    if callback.bot:
        await callback.bot.send_message(
            chat_id=chat_id,
            text="Сообщи об ошибке, описав проблему, с которой ты столкнулся."
        )
    await callback.answer()
