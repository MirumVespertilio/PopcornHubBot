import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from config import config
from handlers import routers

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WEBHOOK_PATH = config.webhook_path
WEBHOOK_URL = config.webhook_base_url.rstrip("/") + WEBHOOK_PATH

dp = Dispatcher(storage=MemoryStorage())

for router in routers:
    dp.include_router(router)

bot = Bot(config.bot_token)


async def on_startup(bot: Bot):
    """Установка вебхука при запуске приложения"""
    try:
        logger.info(f"Устанавливаю вебхук: {WEBHOOK_URL}")
        await bot.set_webhook(WEBHOOK_URL)
        webhook_info = await bot.get_webhook_info()
        logger.info(f"Вебхук установлен: {webhook_info.url}")
        if webhook_info.pending_update_count > 0:
            logger.warning(
                f"Есть {webhook_info.pending_update_count} необработанных апдейтов")
    except Exception as e:
        logger.error(f"Ошибка при установке вебхука: {e}", exc_info=True)


async def on_shutdown(bot: Bot):
    """Удаление вебхука при остановке приложения"""
    try:
        logger.info("Удаляю вебхук...")
        await bot.delete_webhook()
        logger.info("Вебхук удален")
    except Exception as e:
        logger.error(f"Ошибка при удалении вебхука: {e}", exc_info=True)


def create_app():
    app = web.Application()
    SimpleRequestHandler(dp, bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot, on_startup=[
                      on_startup], on_shutdown=[on_shutdown])
    return app


if __name__ == "__main__":
    print("WEBHOOK_URL:", WEBHOOK_URL)
    print("WEBHOOK_PATH:", WEBHOOK_PATH)

    app = create_app()
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
