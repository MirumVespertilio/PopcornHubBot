from aiogram.fsm.state import State, StatesGroup


class Preferences(StatesGroup):
    choosing_type = State()
    choosing_age_limit = State()
    choosing_genre = State()
    choosing_mood = State()
    choosing_year = State()
    viewing_results = State()
    # choosing_rating = State()


class SearchByName(StatesGroup):
    waiting_for_query = State()
    viewing_results = State()
