import asyncio
from typing import Any, Dict, Optional

import aiohttp

from config import config

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=25, connect=10)


class GeminiClient:
    """Асинхронный клиент для обращения к Google Gemini API."""

    def __init__(self) -> None:
        self.api_key = config.gemini_api_key
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=5, limit_per_host=5)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=REQUEST_TIMEOUT,
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def generate_json(self, prompt: str) -> Optional[str]:
        """
        Отправляет prompt в Gemini и возвращает текстовый JSON-ответ.
        Возвращает None при ошибке или отсутствии ключа.
        """
        if not self.api_key:
            print("Gemini API key is not configured.")
            return None

        payload: Dict[str, Any] = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
            }
        }

        session = await self._get_session()
        try:
            async with session.post(
                GEMINI_URL,
                params={"key": self.api_key},
                json=payload,
            ) as response:
                if response.status != 200:
                    body = await response.text()
                    print(f"Gemini API error {response.status}: {body}")
                    return None

                data = await response.json()
                return self._extract_text(data)
        except asyncio.TimeoutError:
            print("Gemini API request timed out.")
            return None
        except Exception as exc:
            print(f"Gemini API request failed: {exc}")
            return None

    @staticmethod
    def _extract_text(data: Dict[str, Any]) -> Optional[str]:
        """
        Извлекает текст из ответа Gemini.
        """
        try:
            candidates = data.get("candidates", [])
            if not candidates:
                return None
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                return None
            return parts[0].get("text")
        except Exception:
            return None


gemini_client = GeminiClient()

