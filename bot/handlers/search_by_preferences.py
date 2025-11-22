from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from states import Preferences


router = Router()

# Константы для жанров
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

CONTENT_TYPES = {
    "want_movie": "фильм",
    "want_series": "сериал",
    "dont_know": "любой"
}

AGE_LIMITS = [
    ("0+", "age_0"),
    ("6+", "age_6"),
    ("12+", "age_12"),
    ("16+", "age_16"),
    ("18+", "age_18"),
    ("🤷 Любой", "age_any"),
]

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
    if not callback.message or not isinstance(callback.message, Message):
        await callback.answer("Ошибка: Сообщение не найдено", show_alert=True)
        return

    # Store chat_id before deleting
    chat_id = callback.message.chat.id

    # Delete the welcome message
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
    if not callback.data or not callback.message:
        await callback.answer()
        return

    # Delete the "Ответь на несколько вопросов..." message
    if isinstance(callback.message, Message):
        await callback.message.delete()

    content_type = CONTENT_TYPES[callback.data]
    await state.update_data(content_type=content_type, selected_genres=[])

    # Create age limit keyboard
    age_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=age_text, callback_data=age_callback)]
            for age_text, age_callback in AGE_LIMITS
        ]
    )

    # Send new message using bot instance
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
    if not callback.data or not callback.message:
        await callback.answer()
        return

    # Delete the age limit selection message
    if isinstance(callback.message, Message):
        await callback.message.delete()

    # Map callback data to age limit value
    age_map = {
        "age_0": "0+",
        "age_6": "6+",
        "age_12": "12+",
        "age_16": "16+",
        "age_18": "18+",
        "age_any": "любой"
    }
    age_limit = age_map.get(callback.data, "любой")
    await state.update_data(age_limit=age_limit)

    genre_kb = build_genre_keyboard([])

    # Send new message using bot instance
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
    if not callback.data or not callback.message:
        await callback.answer()
        return

    data = await state.get_data()
    selected_genres = data.get("selected_genres", [])

    # Обработка "Любой жанр"
    if callback.data == "genre_any_genre":
        await state.update_data(selected_genres=["любой"])
        if isinstance(callback.message, Message):
            await callback.message.delete()

        # Create mood keyboard
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
        if not selected_genres:
            await callback.answer("Выбери хотя бы один жанр или выбери 'Любой жанр'", show_alert=True)
            return

        genres_text = ", ".join(selected_genres)
        if isinstance(callback.message, Message):
            await callback.message.delete()

        # Create mood keyboard
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
    genre_map = {
        callback_data: genre_name for _,
        callback_data, genre_name in GENRES
    }
    genre_name = genre_map.get(callback.data)

    if not genre_name:
        await callback.answer()
        return

    # Переключаем жанр (добавляем или удаляем)
    if genre_name in selected_genres:
        selected_genres.remove(genre_name)
    else:
        selected_genres.append(genre_name)

    await state.update_data(selected_genres=selected_genres)

    # Обновляем клавиатуру и сообщение
    genre_kb = build_genre_keyboard(selected_genres)

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
    if not callback.data or not callback.message:
        await callback.answer()
        return

    # Delete the mood selection message
    if isinstance(callback.message, Message):
        await callback.message.delete()

    # Map callback data to mood value
    mood_map = {
        mood_callback: mood_value for _, mood_callback, mood_value in MOODS
    }
    mood = mood_map.get(callback.data, "любое")
    await state.update_data(mood=mood)

    # Create year keyboard
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
    if not callback.data or not callback.message:
        await callback.answer()
        return

    # Delete the year selection message
    if isinstance(callback.message, Message):
        await callback.message.delete()

    # Map callback data to year value
    year_map = {
        year_callback: year_value for _, year_callback, year_value in YEAR_RANGES
    }
    year = year_map.get(callback.data, "любой")
    await state.update_data(year=year)

    # Year selection complete - ready for search
    if callback.bot and isinstance(callback.message, Message):
        await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text=f"✅ Период выбран: {year}\n\nВсе параметры выбраны! Готов к поиску."
        )

    # Clear state or keep it for search - adjust based on your needs
    # await state.clear()
    await callback.answer()
