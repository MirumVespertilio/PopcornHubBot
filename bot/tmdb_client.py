import aiohttp
from typing import Optional, List, Dict, Any
from config import config

BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


class TMDBClient:
    """Асинхронный клиент для работы с TMDB API"""

    def __init__(self):
        self.api_key = config.tmdb_api_key
        self.language = 'ru-RU'

    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict]:
        """Выполнить запрос к TMDB API"""
        if params is None:
            params = {}

        params['api_key'] = self.api_key
        params['language'] = self.language

        url = f"{BASE_URL}{endpoint}"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"Ошибка API: {response.status}")
                        return None
            except Exception as e:
                print(f"Ошибка запроса: {e}")
                return None

    async def search_movie(self, query: str, page: int = 1) -> List[Dict[str, Any]]:
        """Поиск фильмов по названию"""
        data = await self._make_request("/search/movie", {"query": query, "page": page})
        if data and "results" in data:
            return [self._format_movie_result(m) for m in data["results"]]
        return []

    async def search_tv(self, query: str, page: int = 1) -> List[Dict[str, Any]]:
        """Поиск сериалов по названию"""
        data = await self._make_request("/search/tv", {"query": query, "page": page})
        if data and "results" in data:
            return [self._format_tv_result(t) for t in data["results"]]
        return []

    async def search_all(self, query: str, page: int = 1) -> Dict[str, List[Dict[str, Any]]]:
        """Поиск фильмов и сериалов"""
        movies = await self.search_movie(query, page)
        tv_shows = await self.search_tv(query, page)
        return {"movies": movies, "tv": tv_shows}

    async def discover_movies(
        self,
        genres: Optional[List[int]] = None,
        year: Optional[int] = None,
        year_gte: Optional[int] = None,
        year_lte: Optional[int] = None,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """Поиск фильмов по параметрам"""
        params = {"page": page, "sort_by": "popularity.desc"}

        if genres:
            params["with_genres"] = ",".join(map(str, genres))
        if year:
            params["year"] = year
        if year_gte:
            params["primary_release_date.gte"] = f"{year_gte}-01-01"
        if year_lte:
            params["primary_release_date.lte"] = f"{year_lte}-12-31"

        data = await self._make_request("/discover/movie", params)
        if data and "results" in data:
            return [self._format_movie_result(m) for m in data["results"]]
        return []

    async def discover_tv(
        self,
        genres: Optional[List[int]] = None,
        year: Optional[int] = None,
        year_gte: Optional[int] = None,
        year_lte: Optional[int] = None,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """Поиск сериалов по параметрам"""
        params = {"page": page, "sort_by": "popularity.desc"}

        if genres:
            params["with_genres"] = ",".join(map(str, genres))
        if year:
            params["first_air_date_year"] = year
        if year_gte:
            params["first_air_date.gte"] = f"{year_gte}-01-01"
        if year_lte:
            params["first_air_date.lte"] = f"{year_lte}-12-31"

        data = await self._make_request("/discover/tv", params)
        if data and "results" in data:
            return [self._format_tv_result(t) for t in data["results"]]
        return []

    def _format_movie_result(self, movie_data: Dict) -> Dict[str, Any]:
        """Форматирование данных фильма"""
        poster_path = movie_data.get("poster_path", "")
        return {
            "id": movie_data.get("id"),
            "title": movie_data.get("title", "Без названия"),
            "original_title": movie_data.get("original_title", ""),
            "overview": movie_data.get("overview", "Описание отсутствует"),
            "release_date": movie_data.get("release_date", "Неизвестно"),
            "poster_url": f"{IMAGE_BASE_URL}{poster_path}" if poster_path else "",
            "poster_path": poster_path,
            "backdrop_path": movie_data.get("backdrop_path", ""),
            "vote_average": movie_data.get("vote_average", 0),
            "vote_count": movie_data.get("vote_count", 0),
            "genres": [],  # Будет заполнено при детальном запросе
            "type": "movie"
        }

    def _format_tv_result(self, tv_data: Dict) -> Dict[str, Any]:
        """Форматирование данных сериала"""
        poster_path = tv_data.get("poster_path", "")
        return {
            "id": tv_data.get("id"),
            "title": tv_data.get("name", "Без названия"),
            "original_title": tv_data.get("original_name", ""),
            "overview": tv_data.get("overview", "Описание отсутствует"),
            "release_date": tv_data.get("first_air_date", "Неизвестно"),
            "poster_url": f"{IMAGE_BASE_URL}{poster_path}" if poster_path else "",
            "poster_path": poster_path,
            "backdrop_path": tv_data.get("backdrop_path", ""),
            "vote_average": tv_data.get("vote_average", 0),
            "vote_count": tv_data.get("vote_count", 0),
            "genres": [],  # Будет заполнено при детальном запросе
            "type": "tv"
        }

    @staticmethod
    def get_genre_id(genre_name: str) -> Optional[int]:
        """Получить ID жанра по названию"""
        genre_map = {
            "Драма": 18,
            "Комедия": 35,
            "Детектив": 9648,
            "Фэнтези": 14,
            "Фантастика": 878,
            "Мелодрама": 10749,
            "Ужасы": 27,
            "Триллер": 53,
            "Боевик": 28,
            "Мультфильмы": 16,
        }
        return genre_map.get(genre_name)

    @staticmethod
    def parse_year_range(year_range: str) -> tuple[Optional[int], Optional[int]]:
        """Парсинг диапазона годов"""
        if year_range == "любой":
            return None, None

        if "-" in year_range:
            parts = year_range.split("-")
            if len(parts) == 2:
                try:
                    return int(parts[0]), int(parts[1])
                except ValueError:
                    pass

        if year_range.startswith("до "):
            try:
                year = int(year_range.replace("до ", ""))
                return None, year
            except ValueError:
                pass

        return None, None


# Создаём глобальный экземпляр клиента
tmdb_client = TMDBClient()
