import os
import logging
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.types import Update
from config import config
from handlers import routers

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Убеждаемся, что путь начинается с /
WEBHOOK_PATH = config.webhook_path
if not WEBHOOK_PATH.startswith('/'):
    WEBHOOK_PATH = '/' + WEBHOOK_PATH

WEBHOOK_URL = config.webhook_base_url.rstrip("/") + WEBHOOK_PATH

dp = Dispatcher(storage=MemoryStorage())

# Middleware для логирования всех апдейтов


async def log_updates_middleware(handler, event, data):
    """Логирование всех входящих апдейтов"""
    logger.info(
        f"Получен апдейт: update_id={event.update_id}, type={event.event_type}")
    try:
        result = await handler(event, data)
        logger.info(f"Апдейт {event.update_id} обработан успешно")
        return result
    except Exception as e:
        logger.error(
            f"Ошибка при обработке апдейта {event.update_id}: {e}", exc_info=True)
        raise

dp.update.outer_middleware.register(log_updates_middleware)

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

    # Middleware для логирования всех HTTP запросов
    @web.middleware
    async def log_requests(request, handler):
        logger.info(f"HTTP {request.method} {request.path_qs}")
        try:
            response = await handler(request)
            # Логируем только успешные запросы и ошибки, кроме 404 (это нормально для health checks)
            if response.status == 404:
                logger.debug(
                    f"HTTP {request.method} {request.path_qs} -> 404 (Not Found)")
            else:
                logger.info(
                    f"HTTP {request.method} {request.path_qs} -> {response.status}")
            return response
        except web.HTTPNotFound:
            # 404 - это нормально, не логируем как ошибку
            logger.debug(
                f"HTTP {request.method} {request.path_qs} -> 404 (Not Found)")
            raise
        except Exception as e:
            logger.error(
                f"Ошибка при обработке HTTP запроса {request.path_qs}: {e}", exc_info=True)
            raise

    app.middlewares.append(log_requests)

    # Health check endpoint для Render/UptimeRobot
    async def health_check(request):
        return web.Response(text="OK", status=200)

    app.router.add_get('/', health_check)

    # Регистрируем обработчик вебхука
    logger.info(f"Регистрирую обработчик вебхука по пути: {WEBHOOK_PATH}")
    SimpleRequestHandler(dp, bot).register(app, path=WEBHOOK_PATH)

    setup_application(app, dp, bot=bot, on_startup=[
                      on_startup], on_shutdown=[on_shutdown])
    return app


if __name__ == "__main__":
    print("WEBHOOK_URL:", WEBHOOK_URL)
    print("WEBHOOK_PATH:", WEBHOOK_PATH)
    logger.info("Запуск приложения...")

    app = create_app()
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
