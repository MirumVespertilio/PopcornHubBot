from aiogram.fsm.state import State, StatesGroup

class Preferences(StatesGroup):
    choosing_type = State()
    choosing_rating = State()
    choosing_genre = State()
    choosing_mood = State()
    choosing_year = State()
