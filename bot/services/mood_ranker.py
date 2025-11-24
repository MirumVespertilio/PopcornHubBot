import json
from typing import Any, Dict, List

from services.gemini_client import gemini_client

MAX_RANKED_RESULTS = 15


class MoodRanker:
    """Ранжирует результаты TMDB в соответствии с настроением пользователя."""

    async def rank_by_mood(self, results: List[Dict[str, Any]], mood: str) -> List[Dict[str, Any]]:
        """
        Возвращает список из MAX_RANKED_RESULTS элементов, отсортированных по настроению.
        Если ранжирование недоступно, возвращает входные данные (обрезанные).
        """
        if not results:
            return []

        trimmed = results[:MAX_RANKED_RESULTS]

        normalized_mood = (mood or "").strip().lower()
        if normalized_mood in ("", "любое"):
            return trimmed

        prompt = self._build_prompt(trimmed, mood)
        response_text = await gemini_client.generate_json(prompt)
        if not response_text:
            return trimmed

        try:
            parsed = json.loads(response_text)
        except json.JSONDecodeError:
            print("Gemini JSON parse error.")
            return trimmed

        return self._merge_results(trimmed, parsed)

    def _build_prompt(self, items: List[Dict[str, Any]], mood: str) -> str:
        """Готовит промпт с краткими данными о фильмах/сериалах."""
        payload = []
        for item in items:
            payload.append(
                {
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "type": item.get("type"),
                    "overview": (item.get("overview") or "")[:500],
                    "genres": item.get("genres") or [],
                    "vote_average": item.get("vote_average"),
                    "vote_count": item.get("vote_count"),
                }
            )

        catalog = json.dumps(payload, ensure_ascii=False)
        return (
            "Ты — рекомендательная система, которая помогает выбрать контент под настроение.\n"
            f"Настроение пользователя: {mood}.\n"
            "Перед тобой JSON со списком кандидатов. Для каждого оцени, насколько хорошо он подходит настроению, "
            "и верни JSON формата {\"items\": [{\"id\": <int>, \"score\": <0..1>, \"reason\": \"краткое объяснение\"}, ...]}.\n"
            "Элементы должны идти в порядке убывания score. Если данных недостаточно, сохрани исходный порядок, "
            "но всё равно верни описанный JSON.\n"
            f"Список кандидатов: {catalog}"
        )

    def _merge_results(self, original: List[Dict[str, Any]], response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Объединяет результаты LLM с оригинальными данными."""
        ranked_items = response.get("items")
        if not isinstance(ranked_items, list):
            return original

        id_map = {item.get("id"): item for item in original if item.get("id") is not None}
        used_ids = set()
        ranked_results: List[Dict[str, Any]] = []

        for ranked in ranked_items:
            item_id = ranked.get("id")
            if item_id in used_ids:
                continue
            matched = id_map.get(item_id)
            if not matched:
                continue

            enriched = dict(matched)
            enriched["mood_score"] = ranked.get("score")
            enriched["mood_reason"] = ranked.get("reason")
            ranked_results.append(enriched)
            used_ids.add(item_id)

        for item in original:
            if item.get("id") not in used_ids:
                ranked_results.append(item)

        return ranked_results[:MAX_RANKED_RESULTS]


mood_ranker = MoodRanker()

