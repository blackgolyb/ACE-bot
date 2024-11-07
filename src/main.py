import asyncio
import logging
import sys

import aioschedule
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNetworkError
from aiosqlite import Connection

from src.core.config import get_config
from src.core.modules import ModulesLoader
from src.middlewares import DbSessionMiddleware
from src.utils import try_to_run
from src.db import init_db, get_db


async def scheduler(tasks, bot: Bot, db: Connection):
    for task in tasks:
        await task(bot, db)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(tasks, bot: Bot, db: Connection):
    asyncio.create_task(scheduler(tasks, bot, db))


async def main():
    config = get_config()
    properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
    bot = Bot(token=config.bot.token, default=properties)
    dp = Dispatcher()

    modules_loader = ModulesLoader()
    modules_loader.load()

    db = await get_db()
    dp.include_router(modules_loader.router)
    dp.update.middleware(DbSessionMiddleware(db=db))

    async def _on_startup(bot: Bot):
        await on_startup(modules_loader.tasks, bot, db)
    dp.startup.register(_on_startup)

    await init_db(db)
    await try_to_run(
        coroutine=dp.start_polling(bot),
        attempts=config.bot.attempts,
        sleep=config.bot.attempt_sleep,
        exception=TelegramNetworkError,
    )
    await db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
