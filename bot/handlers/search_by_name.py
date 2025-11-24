from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from states import SearchByName
from services.search_service import search_service
from utils.formatters import format_single_result, format_watch_providers
from tmdb_client import tmdb_client


router = Router()


@router.callback_query(F.data == "search_by_name")
async def search_by_name_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик callback для начала поиска по названию"""
    if not callback.message or not isinstance(callback.message, Message):
        await callback.answer("Ошибка: Сообщение не найдено", show_alert=True)
        return

    # Удаляем приветственное сообщение
    await callback.message.delete()

    # Отправляем сообщение с запросом названия
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    cancel_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="❌ Отмена", callback_data="cancel_search")]
        ]
    )
    prompt_message = await callback.message.answer(
        text="Напиши часть или название фильма/сериала и я помогу найти его🎬✨",
        reply_markup=cancel_kb
    )

    await state.update_data(search_prompt_message_id=prompt_message.message_id)
    await state.set_state(SearchByName.waiting_for_query)
    await callback.answer()


@router.message(SearchByName.waiting_for_query, F.text)
async def process_search_query(msg: Message, state: FSMContext):
    """Обработчик текстового запроса для поиска по названию"""
    data = await state.get_data()
    prompt_message_id = data.get("search_prompt_message_id")
    if prompt_message_id and msg.bot:
        try:
            await msg.bot.delete_message(chat_id=msg.chat.id, message_id=prompt_message_id)
        except Exception:
            pass
        await state.update_data(search_prompt_message_id=None)

    if not msg.text:
        await msg.reply("Пожалуйста, введи название фильма или сериала для поиска.")
        return

    query = msg.text.strip()

    if not query:
        await msg.reply("Пожалуйста, введи название фильма или сериала для поиска.")
        return

    # Отправляем сообщение о поиске
    search_message = await msg.reply("🔍 Ищу...")

    try:
        # Выполняем поиск (по умолчанию ищем и фильмы, и сериалы)
        results = await search_service.search_by_name(query, content_type="любой")

        if not results:
            # Удаляем сообщение "Ищу..."
            try:
                await search_message.delete()
            except Exception:
                pass

            await msg.reply("😔 К сожалению, ничего не найдено. Попробуйте изменить запрос.")
            await state.clear()
            return

        # Ограничиваем количество результатов
        max_results = 20
        display_results = results[:max_results]
        total_count = len(display_results)

        # Сохраняем результаты, текущий индекс и поисковый запрос в состоянии
        await state.update_data(
            results=display_results,
            current_index=0,
            total_count=total_count,
            search_query=query
        )

        # Форматируем первый результат
        result = display_results[0]
        text, poster_url, keyboard = format_single_result(
            result, 0, total_count)

        # Удаляем сообщение "Ищу..."
        try:
            await search_message.delete()
        except Exception:
            pass

        # Отправляем результат с постером
        if poster_url:
            await msg.reply_photo(
                photo=poster_url,
                caption=text,
                reply_markup=keyboard
            )
        else:
            await msg.reply(
                text=text,
                reply_markup=keyboard
            )

        # Переходим в состояние просмотра результатов
        await state.set_state(SearchByName.viewing_results)

    except Exception as e:
        print(f"Ошибка при поиске: {e}")
        # Пытаемся удалить сообщение "Ищу..." (обрабатываем ошибку)
        try:
            await search_message.delete()
        except Exception:
            pass  # Игнорируем ошибку, если сообщение уже удалено

        await msg.reply(
            "😔 Произошла ошибка при поиске. Попробуйте позже или измените запрос."
        )
        await state.clear()


@router.callback_query(SearchByName.waiting_for_query, F.data == "cancel_search")
async def cancel_search_by_name_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик отмены поиска по названию во время ожидания запроса"""
    from handlers.start import show_main_menu
    await show_main_menu(callback, state)
    await callback.answer()


@router.callback_query(SearchByName.viewing_results, F.data.in_(["result_prev", "result_next"]))
async def navigate_results(callback: CallbackQuery, state: FSMContext):
    """Обработчик навигации по результатам поиска"""
    if not callback.message or not isinstance(callback.message, Message) or not callback.data:
        await callback.answer()
        return

    data = await state.get_data()
    results = data.get("results", [])
    current_index = data.get("current_index", 0)
    total_count = data.get("total_count", len(results))

    if not results:
        await callback.answer("Результаты не найдены", show_alert=True)
        return

    # Определяем направление навигации
    if callback.data == "result_prev":
        new_index = current_index - 1
    elif callback.data == "result_next":
        new_index = current_index + 1
    else:
        await callback.answer()
        return

    # Проверяем границы
    if new_index < 0 or new_index >= total_count:
        await callback.answer()
        return

    # Обновляем индекс
    await state.update_data(current_index=new_index)

    # Получаем новый результат
    result = results[new_index]
    text, poster_url, keyboard = format_single_result(
        result, new_index, total_count)

    # Обновляем сообщение
    try:
        if poster_url:
            await callback.message.edit_media(
                media=InputMediaPhoto(media=poster_url, caption=text),
                reply_markup=keyboard
            )
        else:
            await callback.message.edit_text(
                text=text,
                reply_markup=keyboard
            )
    except Exception as e:
        print(f"Ошибка при обновлении сообщения: {e}")
        # Если не удалось обновить, отправляем новое
        if poster_url:
            await callback.message.answer_photo(
                photo=poster_url,
                caption=text,
                reply_markup=keyboard
            )
        else:
            await callback.message.answer(
                text=text,
                reply_markup=keyboard
            )

    await callback.answer()


@router.callback_query(SearchByName.viewing_results, F.data == "finish_search")
async def finish_search_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик завершения поиска - показывает стриминговые сервисы"""
    if not callback.message or not isinstance(callback.message, Message):
        await callback.answer("Ошибка: Сообщение не найдено", show_alert=True)
        return

    data = await state.get_data()
    results = data.get("results", [])
    current_index = data.get("current_index", 0)

    if not results or current_index >= len(results):
        await callback.answer("Результаты не найдены", show_alert=True)
        return

    # Получаем текущий результат
    result = results[current_index]
    content_id = result.get("id")
    content_type = result.get("type", "movie")  # "movie" или "tv"
    title = result.get("title", "Без названия")

    # Отправляем сообщение о загрузке
    loading_msg = await callback.message.answer("🔍 Ищу доступные стриминговые сервисы...")

    try:
        # Получаем информацию о стриминговых сервисах
        providers_data = await tmdb_client.get_watch_providers(
            content_id=content_id,
            content_type=content_type,
            country="RU"
        )

        # Удаляем сообщение о загрузке
        try:
            await loading_msg.delete()
        except Exception:
            pass

        # Форматируем и отправляем список сервисов
        text, keyboard = format_watch_providers(providers_data, title)

        # Удаляем текущее сообщение с результатом
        try:
            await callback.message.delete()
        except Exception:
            pass

        # Отправляем сообщение со списком сервисов
        await callback.message.answer(text=text, reply_markup=keyboard)

    except Exception as e:
        print(f"Ошибка при получении стриминговых сервисов: {e}")
        # Удаляем сообщение о загрузке
        try:
            await loading_msg.delete()
        except Exception:
            pass

        # Отправляем сообщение об ошибке
        text, keyboard = format_watch_providers(None, title)
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(text=text, reply_markup=keyboard)

    await callback.answer()


@router.callback_query(SearchByName.viewing_results, F.data == "back_to_search")
async def back_to_search_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик возврата к результатам поиска по названию"""
    if not callback.message or not isinstance(callback.message, Message):
        await callback.answer("Ошибка: Сообщение не найдено", show_alert=True)
        return

    data = await state.get_data()
    results = data.get("results", [])
    current_index = data.get("current_index", 0)
    total_count = data.get("total_count", len(results))

    if not results:
        await callback.answer("Результаты поиска не найдены", show_alert=True)
        return

    # Получаем текущий результат
    result = results[current_index]
    text, poster_url, keyboard = format_single_result(
        result, current_index, total_count)

    # Удаляем текущее сообщение
    try:
        await callback.message.delete()
    except Exception:
        pass

    # Отправляем результат
    if poster_url:
        await callback.message.answer_photo(
            photo=poster_url,
            caption=text,
            reply_markup=keyboard
        )
    else:
        await callback.message.answer(
            text=text,
            reply_markup=keyboard
        )

    # Восстанавливаем состояние просмотра результатов
    await state.set_state(SearchByName.viewing_results)
    await callback.answer()
