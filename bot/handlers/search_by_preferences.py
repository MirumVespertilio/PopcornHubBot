from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from states import Preferences
from services.search_service import search_service
from utils.formatters import format_single_result


router = Router()

# Константы для жанров (отображаемый текст, callback_data, название жанра)
GENRES = [
    ("🎭 Драма", "genre_drama", "Драма"),
    ("🤣 Комедия", "genre_comedy", "Комедия"),
    ("🔍 Детектив", "genre_detective", "Детектив"),
    ("🧙 Фэнтези", "genre_fantasy", "Фэнтези"),
    ("🚀 Фантастика", "genre_sci_fi", "Фантастика"),
    ("💕 Мелодрама", "genre_romance", "Мелодрама"),
    ("😱 Ужасы", "genre_horror", "Ужасы"),
    ("🔪 Триллер", "genre_thriller", "Триллер"),
    ("💥 Боевик", "genre_action", "Боевик"),
    ("🏰 Мультфильмы", "genre_cartoon", "Мультфильмы"),
]

# Словарь соответствия callback_data типу контента
CONTENT_TYPES = {
    "want_movie": "фильм",
    "want_series": "сериал",
    "dont_know": "любой"
}

# Возрастные рейтинги (отображаемый текст, callback_data)
AGE_LIMITS = [
    ("0+", "age_0"),
    ("6+", "age_6"),
    ("12+", "age_12"),
    ("16+", "age_16"),
    ("18+", "age_18"),
    ("🤷 Любой", "age_any"),
]

# Настроения (отображаемый текст, callback_data, значение настроения)
MOODS = [
    ("😊 Хочу посмеяться", "mood_happy", "весёлое"),
    ("😢 Хочу поплакать", "mood_sad", "грустное"),
    ("🤔 Хочу подумать", "mood_thoughtful", "заставляющее думать"),
    ("😱 Хочу испугаться", "mood_scared", "страшное"),
    ("💪 Хочу вдохновиться", "mood_inspired", "вдохновляющее"),
    ("😴 Хочу расслабиться", "mood_relaxed", "расслабляющее"),
    ("🎬 Хочу захватывающее", "mood_excited", "захватывающее"),
    ("🤷 Любое настроение", "mood_any", "любое"),
]

# Периоды выпуска (отображаемый текст, callback_data, значение периода)
YEAR_RANGES = [
    ("2020-2025", "year_2020_2025", "2020-2025"),
    ("2010-2019", "year_2010_2019", "2010-2019"),
    ("2000-2009", "year_2000_2009", "2000-2009"),
    ("1990-1999", "year_1990_1999", "1990-1999"),
    ("1980-1989", "year_1980_1989", "1980-1989"),
    ("1970-1979", "year_1970_1979", "1970-1979"),
    ("До 1970", "year_before_1970", "до 1970"),
    ("🤷 Любой год", "year_any", "любой"),
]


def build_genre_keyboard(selected_genres: list[str]) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру выбора жанров с отметками выбранных."""
    buttons = []
    for emoji_text, callback_data, genre_name in GENRES:
        text = f"✅ {emoji_text}" if genre_name in selected_genres else emoji_text
        buttons.append([InlineKeyboardButton(
            text=text, callback_data=callback_data)])

    buttons.append([InlineKeyboardButton(
        text="🤷 Любой жанр", callback_data="genre_any_genre")])
    buttons.append([InlineKeyboardButton(
        text="✅ Готово", callback_data="genre_done")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data == "search_by_preferences")
async def search_by_preferences_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик начала поиска по предпочтениям. Запускает процесс выбора параметров."""
    if not callback.message or not isinstance(callback.message, Message):
        await callback.answer("Ошибка: Сообщение не найдено", show_alert=True)
        return

    # Сохраняем chat_id перед удалением (на случай, если понадобится)
    chat_id = callback.message.chat.id

    # Удаляем приветственное сообщение
    await callback.message.delete()

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎥 Хочу фильм", callback_data="want_movie"
                ),
                InlineKeyboardButton(
                    text="📺 Хочу сериал", callback_data="want_series"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🤷 Пока не знаю", callback_data="dont_know"
                )]
        ]
    )

    await callback.message.answer(
        text="Ответь на несколько вопросов — и я найду тебе то, что стоит посмотреть 🎬✨",
        reply_markup=inline_kb
    )
    await state.set_state(Preferences.choosing_type)
    await callback.answer()


@router.callback_query(Preferences.choosing_type, F.data.in_(["want_movie", "want_series", "dont_know"]))
async def content_type_chosen(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора типа контента (фильм/сериал/не знаю)."""
    if not callback.data or not callback.message:
        await callback.answer()
        return

    # Delete the "Ответь на несколько вопросов..." message
    if isinstance(callback.message, Message):
        await callback.message.delete()

    # Получаем тип контента из словаря
    content_type = CONTENT_TYPES[callback.data]
    # Сохраняем тип контента и инициализируем пустой список выбранных жанров
    await state.update_data(content_type=content_type, selected_genres=[])

    # Создаём клавиатуру выбора возрастного рейтинга
    age_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=age_text, callback_data=age_callback)]
            for age_text, age_callback in AGE_LIMITS
        ]
    )

    # Отправляем новое сообщение через экземпляр бота
    if callback.bot and isinstance(callback.message, Message):
        await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text="🎯 Выбери возрастной рейтинг:",
            reply_markup=age_kb
        )

    await state.set_state(Preferences.choosing_age_limit)
    await callback.answer()


@router.callback_query(Preferences.choosing_age_limit, F.data.startswith("age_"))
async def age_limit_chosen(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора возрастного рейтинга."""
    if not callback.data or not callback.message:
        await callback.answer()
        return

    # Удаляем сообщение выбора возрастного рейтинга
    if isinstance(callback.message, Message):
        await callback.message.delete()

    # Преобразуем callback data в значение возрастного рейтинга
    age_map = {
        "age_0": "0+",
        "age_6": "6+",
        "age_12": "12+",
        "age_16": "16+",
        "age_18": "18+",
        "age_any": "любой"
    }
    age_limit = age_map.get(callback.data, "любой")
    # Сохраняем выбранный возрастной рейтинг
    await state.update_data(age_limit=age_limit)

    # Создаём клавиатуру выбора жанров (пока без выбранных жанров)
    genre_kb = build_genre_keyboard([])

    # Отправляем новое сообщение через экземпляр бота
    if callback.bot and isinstance(callback.message, Message):
        await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text="📌 Выбери один или несколько жанров:",
            reply_markup=genre_kb
        )

    await state.set_state(Preferences.choosing_genre)
    await callback.answer()


@router.callback_query(Preferences.choosing_genre, F.data.startswith("genre_"))
async def genre_selection_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора жанров. Поддерживает множественный выбор и переключение."""
    if not callback.data or not callback.message:
        await callback.answer()
        return

    # Получаем текущие данные состояния и список выбранных жанров
    data = await state.get_data()
    selected_genres = data.get("selected_genres", [])

    # Обработка "Любой жанр"
    if callback.data == "genre_any_genre":
        # Сохраняем "любой" как выбранный жанр
        await state.update_data(selected_genres=["любой"])
        if isinstance(callback.message, Message):
            await callback.message.delete()

        # Создаём клавиатуру выбора настроения
        mood_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text=mood_text, callback_data=mood_callback)]
                for mood_text, mood_callback, _ in MOODS
            ]
        )

        if callback.bot and isinstance(callback.message, Message):
            await callback.bot.send_message(
                chat_id=callback.message.chat.id,
                text="🎭 Какое у тебя сейчас настроение?",
                reply_markup=mood_kb
            )
        await state.set_state(Preferences.choosing_mood)
        await callback.answer("Выбран любой жанр")
        return

    # Обработка "Готово"
    if callback.data == "genre_done":
        # Проверяем, что хотя бы один жанр выбран
        if not selected_genres:
            await callback.answer("Выбери хотя бы один жанр или выбери 'Любой жанр'", show_alert=True)
            return

        genres_text = ", ".join(selected_genres)
        if isinstance(callback.message, Message):
            await callback.message.delete()

        # Создаём клавиатуру выбора настроения
        mood_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text=mood_text, callback_data=mood_callback)]
                for mood_text, mood_callback, _ in MOODS
            ]
        )

        if callback.bot and isinstance(callback.message, Message):
            await callback.bot.send_message(
                chat_id=callback.message.chat.id,
                text="🎭 Какое у тебя сейчас настроение?",
                reply_markup=mood_kb
            )
        await state.set_state(Preferences.choosing_mood)
        await callback.answer()
        return

    # Обработка выбора конкретного жанра
    # Создаём словарь для преобразования callback_data в название жанра
    genre_map = {
        callback_data: genre_name for _,
        callback_data, genre_name in GENRES
    }
    genre_name = genre_map.get(callback.data)

    if not genre_name:
        await callback.answer()
        return

    # Переключаем жанр (добавляем или удаляем из списка)
    if genre_name in selected_genres:
        selected_genres.remove(genre_name)
    else:
        selected_genres.append(genre_name)

    # Сохраняем обновлённый список выбранных жанров
    await state.update_data(selected_genres=selected_genres)

    # Обновляем клавиатуру и сообщение с актуальным списком выбранных жанров
    genre_kb = build_genre_keyboard(selected_genres)

    # Формируем текст сообщения в зависимости от количества выбранных жанров
    if selected_genres:
        genres_list = ", ".join(selected_genres)
        status_text = f"📌 Выбрано жанров: {len(selected_genres)}\n{genres_list}\n\nВыбери ещё или нажми 'Готово':"
    else:
        status_text = "📌 Выбери один или несколько жанров (можно выбрать несколько):"

    if isinstance(callback.message, Message):
        await callback.message.edit_text(text=status_text, reply_markup=genre_kb)
    await callback.answer()


@router.callback_query(Preferences.choosing_mood, F.data.startswith("mood_"))
async def mood_chosen(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора настроения."""
    if not callback.data or not callback.message:
        await callback.answer()
        return

    # Удаляем сообщение выбора настроения
    if isinstance(callback.message, Message):
        await callback.message.delete()

    # Преобразуем callback data в значение настроения
    mood_map = {
        mood_callback: mood_value for _, mood_callback, mood_value in MOODS
    }
    mood = mood_map.get(callback.data, "любое")
    # Сохраняем выбранное настроение
    await state.update_data(mood=mood)

    # Создаём клавиатуру выбора периода выпуска
    year_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=year_text, callback_data=year_callback)]
            for year_text, year_callback, _ in YEAR_RANGES
        ]
    )

    if callback.bot and isinstance(callback.message, Message):
        await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text="📅 Выбери период выпуска:",
            reply_markup=year_kb
        )

    await state.set_state(Preferences.choosing_year)
    await callback.answer()


@router.callback_query(Preferences.choosing_year, F.data.startswith("year_"))
async def year_chosen(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора периода выпуска. Завершает процесс выбора параметров."""
    if not callback.data or not callback.message:
        await callback.answer()
        return

    # Удаляем сообщение выбора периода выпуска
    if isinstance(callback.message, Message):
        await callback.message.delete()

    # Преобразуем callback data в значение периода выпуска
    year_map = {
        year_callback: year_value for _, year_callback, year_value in YEAR_RANGES
    }
    year = year_map.get(callback.data, "любой")
    # Сохраняем выбранный период выпуска
    await state.update_data(year=year)

    # Получаем все собранные данные из состояния
    data = await state.get_data()
    content_type = data.get("content_type", "любой")
    selected_genres = data.get("selected_genres", [])
    mood = data.get("mood", "любое")
    age_limit = data.get("age_limit", "любой")

    # Инициализируем search_message как None
    search_message = None

    # Отправляем сообщение о начале поиска
    if callback.bot and isinstance(callback.message, Message):
        search_message = await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text="🔍 Ищу подходящие фильмы и сериалы..."
        )

    try:
        # Формируем словарь предпочтений для поиска
        preferences = {
            "content_type": content_type,
            "genres": selected_genres,
            "year": year,
            "mood": mood,  # Для будущего использования с GroqAI
            "age_limit": age_limit  # Для будущего использования
        }

        # Выполняем поиск
        results = await search_service.search_by_preferences(preferences)

        if not results:
            # Удаляем сообщение "Ищу..."
            if callback.bot and isinstance(callback.message, Message):
                if search_message:
                    try:
                        await search_message.delete()
                    except Exception:
                        pass

                await callback.bot.send_message(
                    chat_id=callback.message.chat.id,
                    text="😔 К сожалению, ничего не найдено. Попробуйте изменить параметры поиска."
                )
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

        # Удаляем сообщение "Ищу..." и отправляем результаты
        if callback.bot and isinstance(callback.message, Message):
            # Пытаемся удалить сообщение "Ищу..." (обрабатываем ошибку)
            if search_message:
                try:
                    await search_message.delete()
                except Exception:
                    pass  # Игнорируем ошибку, если сообщение уже удалено

            # Отправляем результат с постером
            if poster_url:
                await callback.bot.send_photo(
                    chat_id=callback.message.chat.id,
                    photo=poster_url,
                    caption=text,
                    reply_markup=keyboard
                )
            else:
                await callback.bot.send_message(
                    chat_id=callback.message.chat.id,
                    text=text,
                    reply_markup=keyboard
                )

        # Переходим в состояние просмотра результатов
        await state.set_state(Preferences.viewing_results)

    except Exception as e:
        print(f"Ошибка при поиске по предпочтениям: {e}")
        if callback.bot and isinstance(callback.message, Message):
            # Пытаемся удалить сообщение "Ищу..." (обрабатываем ошибку)
            if search_message:
                try:
                    await search_message.delete()
                except Exception:
                    pass  # Игнорируем ошибку, если сообщение уже удалено

            await callback.bot.send_message(
                chat_id=callback.message.chat.id,
                text="😔 Произошла ошибка при поиске. Попробуйте позже или измените параметры."
            )
        await state.clear()


@router.callback_query(Preferences.viewing_results, F.data.in_(["result_prev", "result_next"]))
async def navigate_preferences_results(callback: CallbackQuery, state: FSMContext):
    """Обработчик навигации по результатам поиска по предпочтениям"""
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
        if callback.bot and isinstance(callback.message, Message):
            if poster_url:
                await callback.bot.send_photo(
                    chat_id=callback.message.chat.id,
                    photo=poster_url,
                    caption=text,
                    reply_markup=keyboard
                )
            else:
                await callback.bot.send_message(
                    chat_id=callback.message.chat.id,
                    text=text,
                    reply_markup=keyboard
                )

    await callback.answer()

    await callback.answer()
