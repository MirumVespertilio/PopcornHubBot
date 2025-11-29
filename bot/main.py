import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from config import config
from handlers import routers


WEBHOOK_PATH = config.webhook_path
WEBHOOK_URL = config.webhook_base_url.rstrip("/") + WEBHOOK_PATH


dp = Dispatcher(storage=MemoryStorage())


for router in routers:
    dp.include_router(router)

bot = Bot(config.bot_token)

async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(bot: Bot):
    await bot.delete_webhook()


def create_app():
    app = web.Application()
    SimpleRequestHandler(dp, bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    return app


if __name__ == "__main__":
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
