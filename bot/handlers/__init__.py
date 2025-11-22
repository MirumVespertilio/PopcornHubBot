from .start import router as start_router
from .search_by_preferences import router as search_by_preferences_router
from .search_by_name import router as search_by_name_router


routers = [start_router, search_by_preferences_router, search_by_name_router]
