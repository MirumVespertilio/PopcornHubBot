import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from config import config
from handlers import routers

# Убеждаемся, что путь начинается с /
WEBHOOK_PATH = config.webhook_path
if not WEBHOOK_PATH.startswith('/'):
    WEBHOOK_PATH = '/' + WEBHOOK_PATH

WEBHOOK_URL = config.webhook_base_url.rstrip("/") + WEBHOOK_PATH

dp = Dispatcher(storage=MemoryStorage())

for router in routers:
    dp.include_router(router)

bot = Bot(config.bot_token)


async def on_startup(bot: Bot):
    """Установка вебхука при запуске приложения"""
    await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(bot: Bot):
    """Удаление вебхука при остановке приложения"""
    await bot.delete_webhook()


def create_app():
    app = web.Application()

    # Регистрируем обработчик вебхука
    SimpleRequestHandler(dp, bot).register(app, path=WEBHOOK_PATH)

    setup_application(app, dp, bot=bot, on_startup=[on_startup], on_shutdown=[on_shutdown])
    return app


if __name__ == "__main__":
    print("WEBHOOK_URL:", WEBHOOK_URL)
    print("WEBHOOK_PATH:", WEBHOOK_PATH)

    app = create_app()
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
