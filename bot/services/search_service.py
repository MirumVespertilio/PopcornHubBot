from typing import Optional, List, Dict, Any
from tmdb_client import tmdb_client


class SearchService:
    """Сервис для поиска контента через TMDB API"""

    async def search_by_name(
        self,
        query: str,
        content_type: str = "любой"
    ) -> List[Dict[str, Any]]:
        """
        Поиск по названию

        Args:
            query: Поисковый запрос
            content_type: "фильм", "сериал" или "любой"

        Returns:
            Список результатов поиска
        """
        try:
            if content_type == "фильм":
                results = await tmdb_client.search_movie(query)
            elif content_type == "сериал":
                results = await tmdb_client.search_tv(query)
            else:  # "любой"
                search_results = await tmdb_client.search_all(query)
                # Объединяем фильмы и сериалы
                results = search_results.get(
                    "movies", []) + search_results.get("tv", [])
                # Сортируем по популярности (vote_average * vote_count)
                results.sort(key=lambda x: x.get("vote_average", 0)
                             * x.get("vote_count", 0), reverse=True)

            return results
        except Exception as e:
            print(f"Ошибка поиска по названию: {e}")
            return []

    async def search_by_preferences(
        self,
        preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Поиск по предпочтениям пользователя

        Args:
            preferences: Словарь с предпочтениями:
                - content_type: "фильм", "сериал" или "любой"
                - genres: список названий жанров (может быть ["любой"])
                - year: строка с диапазоном годов или "любой"
                - mood: настроение (пока не используется, для будущего GroqAI)
                - age_limit: возрастной рейтинг (пока не используется)

        Returns:
            Список результатов поиска
        """
        try:
            content_type = preferences.get("content_type", "любой")
            genres = preferences.get("genres", [])
            year = preferences.get("year", "любой")

            # Преобразуем жанры в TMDB IDs
            genre_ids = []
            if genres and "любой" not in genres:
                for genre_name in genres:
                    genre_id = tmdb_client.get_genre_id(genre_name)
                    if genre_id:
                        genre_ids.append(genre_id)

            # Парсим диапазон годов
            year_gte, year_lte = tmdb_client.parse_year_range(year)

            results = []

            if content_type == "фильм" or content_type == "любой":
                movie_results = await tmdb_client.discover_movies(
                    genres=genre_ids if genre_ids else None,
                    year_gte=year_gte,
                    year_lte=year_lte
                )
                results.extend(movie_results)

            if content_type == "сериал" or content_type == "любой":
                tv_results = await tmdb_client.discover_tv(
                    genres=genre_ids if genre_ids else None,
                    year_gte=year_gte,
                    year_lte=year_lte
                )
                results.extend(tv_results)

            # Сортируем по популярности
            results.sort(key=lambda x: x.get("vote_average", 0)
                         * x.get("vote_count", 0), reverse=True)

            return results
        except Exception as e:
            print(f"Ошибка поиска по предпочтениям: {e}")
            return []


# Создаём глобальный экземпляр сервиса
search_service = SearchService()
