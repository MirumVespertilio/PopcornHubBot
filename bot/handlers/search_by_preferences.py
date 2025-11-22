from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from states import Preferences


router = Router()


@router.callback_query(F.data == "search_by_preferences")
async def search_by_preferences_handler(callback: CallbackQuery, state: FSMContext):
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
    if callback.message:
        await callback.message.answer(
            text="Ответь на несколько вопросов — и я найду тебе то, что стоит посмотреть 🎬✨",
            reply_markup=inline_kb
        )
    else:
        await callback.answer(
            text="Ошибка: Сообщение не найдено",
            show_alert=True
        )
    
    await state.set_state(Preferences.choosing_type)
    await callback.answer()


# Обработчик выбора типа контента
@router.callback_query(Preferences.choosing_type, F.data.in_(["want_movie", "want_series", "dont_know"]))
async def content_type_chosen(callback: CallbackQuery, state: FSMContext):
    content_type_map = {
        "want_movie": "фильм",
        "want_series": "сериал", 
        "dont_know": "любой"
    }
    
    content_type = content_type_map[callback.data]
    
    # Сохраняем в состояние
    await state.update_data(content_type=content_type)
    
    # Предлагаем выбрать жанр
    genre_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎭 Драма", callback_data="drama")],
            [InlineKeyboardButton(text="🤣 Комедия", callback_data="comedy")],
            [InlineKeyboardButton(text="🔍 Детектив", callback_data="detective")],
            [InlineKeyboardButton(text="🧙 Фэнтези", callback_data="fantasy")],
            [InlineKeyboardButton(text="🚀 Фантастика", callback_data="sci_fi")],
            [InlineKeyboardButton(text="💕 Мелодрама", callback_data="romance")],
            [InlineKeyboardButton(text="😱 Ужасы", callback_data="horror")],
            [InlineKeyboardButton(text="🔪 Триллер", callback_data="thriller")],
            [InlineKeyboardButton(text="💥 Боевик", callback_data="action")],
            [InlineKeyboardButton(text="🏰 Мультфильмы", callback_data="cartoon")],
            [InlineKeyboardButton(text="🤷 Любой жанр", callback_data="any_genre")],
        ]
    )
    if callback.message:
        await callback.message.answer(
            text="📌 Какой жанр тебе ближе всего?",
            reply_markup=genre_kb
        )
    else:
        await callback.answer(
            text="Ошибка: Сообщение не найдено",
            show_alert=True
        )
    
    # Переходим к следующему состоянию
    await state.set_state(Preferences.choosing_rating)
    await callback.answer()