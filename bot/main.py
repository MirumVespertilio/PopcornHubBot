import asyncio
from aiogram import Bot, Dispatcher
from config import config
from handlers import routers


dp = Dispatcher()


for router in routers:
    dp.include_router(router)


async def main() -> None:
    bot = Bot(config.bot_token)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
