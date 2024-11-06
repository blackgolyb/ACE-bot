import re
import json

import httpx
from aiogram import Bot
from aiosqlite import Connection


headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/jxl,image/webp,image/png,image/svg+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

class PublisherSevice:
    def __init__(self, db: Connection, bot: Bot | None = None):
        self.db = db
        self.bot = bot

    async def map_publisher(self, chat_id: int, playlist_id: str):
        await self.db.execute(
            """
            INSERT OR IGNORE INTO PlaylistMapping(chat_id, playlist_id, last_video_id) VALUES(?1, ?2, ?3)
            """,
            [chat_id, playlist_id, None]
        )
        await self.db.commit()

    async def get_mappings(self):
        cursor = await self.db.execute(
            """
            SELECT chat_id, playlist_id, last_video_id FROM PlaylistMapping
            """
        )
        rows = await cursor.fetchall()
        await cursor.close()

        return rows

    async def get_mapping(self, chat_id: int, playlist_id: str):
        cursor = await self.db.execute(
            """
            SELECT
                chat_id
                ,playlist_id
                ,last_video_id
            FROM PlaylistMapping
            WHERE
                chat_id = ?1
                AND
                playlist_id = ?2
            """
            ,
            [chat_id, playlist_id]
        )
        row = await cursor.fetchone()
        await cursor.close()

        return row

    async def set_last_video_id(self, chat_id: int, playlist_id: str, video_id: str):
        await self.db.execute(
            """
            UPDATE PlaylistMapping
            SET last_video_id = ?3
            WHERE
                chat_id = ?1
                AND
                playlist_id = ?2
            """,
            [chat_id, playlist_id, video_id]
        )
        await self.db.commit()

    async def send_videos_to_all_subscribers(self, chat_id: int, playlist_id: str, last_video_id: str, all_videos):
        mapping = await self.get_mapping(chat_id, playlist_id)

        def videos_slice_by_video_id(videos, video_id):
            if video_id is None:
                return videos

            for i, v in enumerate(videos):
                if v["video_id"] == video_id:
                    return videos[i + 1:]

            return videos

        def assebly_video_mesage_text(video):
            url = video["url"]
            title = video["title"]
            return f"{title}\n{url}"

        if not mapping or not self.bot:
            return

        videos = videos_slice_by_video_id(all_videos, last_video_id)

        last_video_id = None
        try:
            for video in videos:
                await self.bot.send_message(chat_id, assebly_video_mesage_text(video), disable_web_page_preview=True)
                last_video_id = video["video_id"]
        except:
            ...

        if last_video_id:
            await self.set_last_video_id(chat_id, playlist_id, last_video_id)

    async def get_videos_data_from_playlist(self, playlist_id: str):
        url = "https://www.youtube.com/playlist"
        params = {"list": playlist_id}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)

        m = re.search(r"var ytInitialData = (\{.+\});</script>", response.text)

        if m is None:
            return []

        try:
            data = json.loads(m.group(1))
            videos = data["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"][0]["playlistVideoListRenderer"]["contents"]
        except Exception as e:
            print(e)
            return []

        def map_video(video):
            video = video["playlistVideoRenderer"]
            video_id = video["videoId"]
            url = f"https://www.youtube.com/watch?v={video_id}&list={playlist_id}"
            title = video["title"]["runs"][0]["text"]
            return {"video_id": video_id, "url": url , "title": title}

        return list(map(map_video, videos))
