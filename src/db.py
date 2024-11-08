import aiosqlite

from src.core.config import get_config


async def get_db() -> aiosqlite.Connection:
    config = get_config()
    return await aiosqlite.connect(config.db.url)


async def init_db(db: aiosqlite.Connection):
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS PlaylistMapping (
            chat_id         INTEGER NOT NULL,
            playlist_id     TEXT NOT NULL,
            last_video_id   TEXT,
            PRIMARY KEY (chat_id, playlist_id)
        );
        """
    )
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS Groups (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL
        );
        """
    )
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS Subjects (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL
        );
        """
    )
    await db.commit()
