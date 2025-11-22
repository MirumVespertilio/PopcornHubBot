import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import MenuButtonCommands
from aiogram.filters import Command
from dotenv import load_dotenv
from os import getenv
from aiogram import F

load_dotenv()

BOT_TOKEN = getenv("BOT_TOKEN")
if BOT_TOKEN is None:
    raise RuntimeError("Environment variable BOT_TOKEN is not set")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    await msg.reply("Привет! Я найду фильм. Введи /search <название> или используй Inline.")


async def main() -> None:
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())