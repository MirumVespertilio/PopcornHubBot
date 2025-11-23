from .start import router as start_router
from .search_by_preferences import router as search_by_preferences_router
from .search_by_name import router as search_by_name_router


# Порядок важен: роутеры с FSM состояниями должны быть первыми
# для правильной обработки сообщений с состояниями
routers = [search_by_name_router, search_by_preferences_router, start_router]
