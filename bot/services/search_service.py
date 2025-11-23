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
                - age_limits: список возрастных рейтингов (["0+", "6+", "12+", "16+", "18+", "любой"])

        Returns:
            Список результатов поиска
        """
        try:
            content_type = preferences.get("content_type", "любой")
            genres = preferences.get("genres", [])
            year = preferences.get("year", "любой")
            age_limits = preferences.get("age_limits", ["любой"])

            # Преобразуем жанры в TMDB IDs
            genre_ids = []
            if genres and "любой" not in genres:
                for genre_name in genres:
                    genre_id = tmdb_client.get_genre_id(genre_name)
                    if genre_id:
                        genre_ids.append(genre_id)

            # Парсим диапазон годов
            year_gte, year_lte = tmdb_client.parse_year_range(year)

            # Если выбран "любой" рейтинг, не фильтруем по рейтингу
            if "любой" in age_limits:
                certifications = [(None, None)]
            else:
                # Преобразуем каждый выбранный рейтинг в формат TMDB
                certifications = []
                for age_limit in age_limits:
                    cert, country = tmdb_client.age_limit_to_certification(
                        age_limit)
                    if cert and country:
                        certifications.append((cert, country))

            # Если нет валидных рейтингов, используем "любой"
            if not certifications:
                certifications = [(None, None)]

            # Сначала собираем все результаты для всех рейтингов
            # Получаем несколько страниц для каждого рейтинга, чтобы было больше данных для сортировки
            all_results = []
            seen_ids = set()  # Для удаления дубликатов
            # Получаем по 3 страницы для каждого рейтинга (до 60 результатов)
            pages_per_rating = 3

            # Выполняем поиск для каждого рейтинга и собираем все результаты
            for certification, certification_country in certifications:
                # Получаем несколько страниц результатов для каждого рейтинга
                for page in range(1, pages_per_rating + 1):
                    has_results = False

                    if content_type == "фильм" or content_type == "любой":
                        movie_results = await tmdb_client.discover_movies(
                            genres=genre_ids if genre_ids else None,
                            year_gte=year_gte,
                            year_lte=year_lte,
                            certification=certification,
                            certification_country=certification_country,
                            page=page
                        )
                        if movie_results:
                            has_results = True
                            # Добавляем только уникальные результаты
                            for movie in movie_results:
                                movie_id = movie.get("id")
                                if movie_id and movie_id not in seen_ids:
                                    seen_ids.add(movie_id)
                                    all_results.append(movie)

                    if content_type == "сериал" or content_type == "любой":
                        tv_results = await tmdb_client.discover_tv(
                            genres=genre_ids if genre_ids else None,
                            year_gte=year_gte,
                            year_lte=year_lte,
                            certification=certification,
                            certification_country=certification_country,
                            page=page
                        )
                        if tv_results:
                            has_results = True
                            # Добавляем только уникальные результаты
                            for tv in tv_results:
                                tv_id = tv.get("id")
                                if tv_id and tv_id not in seen_ids:
                                    seen_ids.add(tv_id)
                                    all_results.append(tv)

                    # Если для этой страницы нет результатов ни для фильмов, ни для сериалов, прекращаем
                    if not has_results:
                        break

            # Теперь объединяем все результаты и сортируем по популярности
            # Сортировка происходит после сбора всех результатов, чтобы результаты
            # из разных рейтингов перемешались по популярности
            # Используем улучшенную формулу сортировки, которая учитывает и оценку, и количество голосов
            # но не дает слишком большой вес количеству голосов (используем логарифм)
            import math

            def sort_key(item):
                vote_avg = item.get("vote_average", 0)
                vote_count = item.get("vote_count", 0)

                # Минимальный порог голосов для учета (чтобы фильмы с 1-2 голосами не были наверху)
                min_votes = 10

                # Если голосов меньше минимума, значительно понижаем приоритет
                if vote_count < min_votes:
                    # Понижаем оценку пропорционально недостатку голосов
                    adjusted_avg = vote_avg * (vote_count / min_votes) * 0.5
                else:
                    adjusted_avg = vote_avg

                # Используем логарифм от количества голосов для более сбалансированной сортировки
                # Это позволяет учитывать популярность, но не дает ей слишком большой вес
                # Логарифм замедляет рост влияния количества голосов
                if vote_count > 0:
                    # Нормализуем логарифм: log10(1000) ≈ 3, делим на 10 для получения значения ~0.3
                    popularity_bonus = math.log10(vote_count + 1) / 10
                else:
                    popularity_bonus = 0

                # Комбинируем оценку и бонус популярности
                # Оценка имеет больший вес, популярность - меньший
                return adjusted_avg + popularity_bonus

            all_results.sort(key=sort_key, reverse=True)

            return all_results
        except Exception as e:
            print(f"Ошибка поиска по предпочтениям: {e}")
            return []


# Создаём глобальный экземпляр сервиса
search_service = SearchService()
