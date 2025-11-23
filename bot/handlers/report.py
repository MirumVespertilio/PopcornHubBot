from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from states import ReportError
from config import config

router = Router()


@router.callback_query(F.data == "report")
async def report_handler(callback: CallbackQuery, state: FSMContext):
    if not callback.message or not isinstance(callback.message, Message):
        await callback.answer("Ошибка: Сообщение не найдено", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🔍 Ошибка поиска",
            callback_data="report_category_search"
        )],
        [InlineKeyboardButton(
            text="📱 Ошибка отображения",
            callback_data="report_category_display"
        )],
        [InlineKeyboardButton(
            text="⚙️ Техническая ошибка",
            callback_data="report_category_technical"
        )],
        [InlineKeyboardButton(
            text="❓ Другая ошибка",
            callback_data="report_category_other"
        )],
        [InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="report_cancel"
        )],
    ])

    await callback.message.edit_text(
        "Выбери категорию ошибки:",
        reply_markup=keyboard
    )
    await state.set_state(ReportError.choosing_category)
    await callback.answer()


@router.callback_query(ReportError.choosing_category, F.data == "report_cancel")
async def cancel_report_from_category(callback: CallbackQuery, state: FSMContext):
    if not callback.message or not isinstance(callback.message, Message):
        await callback.answer("Ошибка: Сообщение не найдено", show_alert=True)
        await state.clear()
        return

    await callback.message.edit_text("Отправка отчета отменена.")
    await state.clear()
    await callback.answer()


@router.callback_query(ReportError.choosing_category, F.data.startswith("report_category_"))
async def process_category(callback: CallbackQuery, state: FSMContext):
    if not callback.message or not isinstance(callback.message, Message):
        await callback.answer("Ошибка: Сообщение не найдено", show_alert=True)
        return

    if not callback.data:
        await callback.answer("Ошибка: Данные не найдены", show_alert=True)
        return

    category = callback.data.replace("report_category_", "")
    category_names = {
        "search": "Ошибка поиска",
        "display": "Ошибка отображения",
        "technical": "Техническая ошибка",
        "other": "Другая ошибка"
    }

    await state.update_data(category=category_names.get(category, "Другая ошибка"))

    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="report_cancel")]
    ])

    await callback.message.edit_text(
        "Опиши проблему подробно:\n\n"
        "• Что произошло?\n"
        "• Что ты ожидал увидеть?\n"
        "• На каком этапе возникла ошибка?",
        reply_markup=cancel_kb
    )

    # Сохраняем message_id сообщения с просьбой для последующего удаления
    await state.update_data(
        prompt_message_id=callback.message.message_id,
        chat_id=callback.message.chat.id
    )
    await state.set_state(ReportError.waiting_for_description)
    await callback.answer()


@router.callback_query(ReportError.waiting_for_description, F.data == "report_cancel")
async def cancel_report_from_description(callback: CallbackQuery, state: FSMContext):
    if not callback.message or not isinstance(callback.message, Message):
        await callback.answer("Ошибка: Сообщение не найдено", show_alert=True)
        await state.clear()
        return

    # Удаляем сообщение с просьбой описать проблему
    data = await state.get_data()
    prompt_message_id = data.get('prompt_message_id')
    chat_id = data.get('chat_id')
    if prompt_message_id and chat_id and callback.bot:
        try:
            await callback.bot.delete_message(chat_id=chat_id, message_id=prompt_message_id)
        except Exception as e:
            print(f"Ошибка удаления сообщения с просьбой: {e}")

    await callback.message.edit_text("Отправка отчета отменена.")
    await state.clear()
    await callback.answer()


@router.message(ReportError.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    if not message.text:
        await message.reply("Пожалуйста, отправь текстовое описание проблемы.")
        return

    if not message.from_user:
        await message.reply("Ошибка: Не удалось определить пользователя.")
        await state.clear()
        return

    data = await state.get_data()

    report_text = (
        f"🔴 Отчет об ошибке\n\n"
        f"📂 Категория: {data.get('category', 'Не указана')}\n"
        f"👤 Пользователь: @{message.from_user.username or 'N/A'}\n"
        f"🆔 ID: {message.from_user.id}\n"
        f"📝 Имя: {message.from_user.first_name or 'N/A'}\n\n"
        f"📄 Описание:\n{message.text}"
    )

    # Отправка в группу для отчетов, если указана
    if config.reports_chat_id and message.bot:
        try:
            await message.bot.send_message(chat_id=config.reports_chat_id, text=report_text)
        except Exception as e:
            print(f"Ошибка отправки отчета в группу: {e}")

    # Удаляем сообщение с просьбой описать проблему
    prompt_message_id = data.get('prompt_message_id')
    chat_id = data.get('chat_id')
    if prompt_message_id and chat_id and message.bot:
        try:
            await message.bot.delete_message(chat_id=chat_id, message_id=prompt_message_id)
        except Exception as e:
            print(f"Ошибка удаления сообщения с просьбой: {e}")

    await message.reply(
        "✅ Спасибо за обратную связь!\n\n"
        "Твой отчет отправлен в группу администраторов. "
        "Мы рассмотрим его в ближайшее время."
    )
    await state.clear()
