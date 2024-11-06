import asyncio
import aioschedule
from aiogram import Bot
from aiosqlite import Connection
from itertools import groupby

from services.publisher import PublisherSevice


async def send_videos(bot: Bot, db: Connection):
    service = PublisherSevice(db, bot)
    data = await service.get_mappings()
    data = groupby(data, lambda r: r[1])
    for (playlist_id, chats) in data:
        videos = await service.get_videos_data_from_playlist(playlist_id)
        for (chat_id, _, last_video_id) in chats:
            await service.send_videos_to_all_subscribers(chat_id, playlist_id, last_video_id, videos)



async def register_send_videos(bot: Bot, db: Connection):
    # aioschedule.every().minute.do(send_videos, bot, db)
    aioschedule.every(10).seconds.do(send_videos, bot, db)


tasks = [register_send_videos]
