from os import getenv
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class Config(BaseModel):
    bot_token: str
    tmdb_api_key: str
    reports_chat_id: int = Field(default=0)


config = Config(
    bot_token=getenv("BOT_TOKEN") or "",
    tmdb_api_key=getenv("TMDB_API_KEY") or "",
    reports_chat_id=int(getenv("REPORTS_CHAT_ID") or "0")
)
