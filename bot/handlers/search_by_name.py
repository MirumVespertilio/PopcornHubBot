from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from states import SearchByName
from services.search_service import search_service
from utils.formatters import format_single_result


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
    await callback.message.answer(
        text="Напиши часть или название фильма/сериала и я помогу найти его🎬✨"
    )

    await state.set_state(SearchByName.waiting_for_query)
    await callback.answer()


@router.message(SearchByName.waiting_for_query, F.text)
async def process_search_query(msg: Message, state: FSMContext):
    """Обработчик текстового запроса для поиска по названию"""
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

        # Сохраняем результаты и текущий индекс в состоянии
        await state.update_data(
            results=display_results,
            current_index=0,
            total_count=total_count
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
