import aiohttp
import asyncio
from typing import Optional, List, Dict, Any
from config import config

BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

# Таймауты для запросов
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30, connect=10)


class TMDBClient:
    """Асинхронный клиент для работы с TMDB API"""

    def __init__(self):
        self.api_key = config.tmdb_api_key
        self.language = 'ru-RU'
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Получить или создать сессию для запросов"""
        if self._session is None or self._session.closed:
            # Ограничиваем количество одновременных соединений
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=REQUEST_TIMEOUT
            )
        return self._session

    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict]:
        """Выполнить запрос к TMDB API"""
        if params is None:
            params = {}

        params['api_key'] = self.api_key
        params['language'] = self.language

        url = f"{BASE_URL}{endpoint}"

        session = await self._get_session()
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Ошибка API: {response.status}")
                    return None
        except asyncio.TimeoutError:
            print(f"Таймаут запроса: {endpoint}")
            return None
        except Exception as e:
            print(f"Ошибка запроса: {e}")
            return None

    async def close(self):
        """Закрыть сессию"""
        if self._session and not self._session.closed:
            await self._session.close()

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
        certification: Optional[str] = None,
        certification_country: Optional[str] = None,
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
        if certification and certification_country:
            # Используем указанный рейтинг и страну для фильтрации
            params["certification"] = certification
            params["certification_country"] = certification_country

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
        certification: Optional[str] = None,
        certification_country: Optional[str] = None,
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
        if certification and certification_country:
            # Для сериалов используем content_ratings с указанной страной
            params["certification"] = certification
            params["certification_country"] = certification_country

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
            "genres": [],
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
            "genres": [],
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
    def format_countries(country_codes: List[str]) -> str:
        """Форматирование списка ISO кодов стран в читаемый формат"""
        if not country_codes:
            return "Неизвестно"

        # Маппинг ISO кодов на названия стран
        country_names = {
            "US": "США",
            "GB": "Великобритания",
            "RU": "Россия",
            "FR": "Франция",
            "DE": "Германия",
            "IT": "Италия",
            "ES": "Испания",
            "CA": "Канада",
            "AU": "Австралия",
            "JP": "Япония",
            "KR": "Южная Корея",
            "CN": "Китай",
            "IN": "Индия",
            "BR": "Бразилия",
            "MX": "Мексика",
        }

        # Преобразуем коды в названия
        # Показываем максимум 3 страны
        names = [country_names.get(code, code) for code in country_codes[:3]]
        result = ", ".join(names)

        if len(country_codes) > 3:
            result += f" и ещё {len(country_codes) - 3}"

        return result

    @staticmethod
    def age_limit_to_certification(age_limit: str) -> tuple[Optional[str], Optional[str]]:
        """
        Преобразует русский возрастной рейтинг в формат TMDB API с указанием страны

        Args:
            age_limit: Русский рейтинг ("0+", "6+", "12+", "16+", "18+", "любой")

        Returns:
            Кортеж (certification, country) для TMDB API или (None, None)
        """
        age_map = {
            "0+": ("G", "US"),
            "6+": ("PG", "US"),
            "12+": ("PG-13", "US"),
            "16+": ("16+", "RU"),
            "18+": ("18", "RU"),
            "любой": (None, None)
        }
        return age_map.get(age_limit, (None, None))

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

    async def get_watch_providers(
        self,
        content_id: int,
        content_type: str,
        country: str = "RU"
    ) -> Optional[Dict[str, Any]]:
        """
        Получить информацию о стриминговых сервисах для фильма или сериала

        Args:
            content_id: ID фильма или сериала в TMDB
            content_type: "movie" или "tv"
            country: Код страны (по умолчанию "RU" для России)

        Returns:
            Словарь с данными о провайдерах для указанной страны или None
        """
        if content_type not in ["movie", "tv"]:
            return None

        endpoint = f"/{content_type}/{content_id}/watch/providers"
        data = await self._make_request(endpoint)

        if data and "results" in data and country in data["results"]:
            return data["results"][country]

        return None


# Создаём глобальный экземпляр клиента
tmdb_client = TMDBClient()
