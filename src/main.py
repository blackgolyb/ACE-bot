import asyncio
import logging
import sys
from typing import Callable, Awaitable, Dict, Any

import aioschedule
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import TelegramObject
from aiogram.exceptions import TelegramNetworkError
from aiosqlite import Connection

from src.core.config import get_config
from src.utils import try_to_run
from src.routes import router
from src.tasks import tasks
from src.db import init_db, get_db


class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, db):
        super().__init__()
        self.db = db

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["db"] = self.db
        return await handler(event, data)


async def scheduler(bot: Bot, db: Connection):
    for taks in tasks:
        await taks(bot, db)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(bot: Bot, db: Connection):
    asyncio.create_task(scheduler(bot, db))


async def main():
    config = get_config()
    properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
    bot = Bot(token=config.bot.token, default=properties)
    dp = Dispatcher()

    db = await get_db()
    dp.include_router(router)
    dp.update.middleware(DbSessionMiddleware(db=db))

    async def _on_startup(bot: Bot):
        await on_startup(bot, db)
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
