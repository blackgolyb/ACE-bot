from dataclasses import dataclass
from aiogram import Bot
from aiosqlite import Connection
from enum import Enum
import datetime
import tempfile


@dataclass
class Group:
    id: int
    name: str


@dataclass
class Subject:
    id: int
    name: str


class LessonTypeEnum(Enum):
    LECTION = 1
    PRACTICE = 2
    SEMINAR = 3


@dataclass
class LessonVideo:
    date: datetime.date
    group: int | None
    subject: int
    type: LessonTypeEnum
    order: int | None


class GroupSevice:
    def __init__(self, db: Connection, bot: Bot | None = None):
        self.db = db
        self.bot = bot

    async def add(self, name: str):
        await self.db.execute(
            """
            INSERT OR IGNORE INTO Groups(name) VALUES(?1)
            """,
            [name]
        )
        await self.db.commit()

    async def get_all(self) -> list[Group]:
        cursor = await self.db.execute(
            """
            SELECT id, name FROM Groups
            """
        )
        rows = await cursor.fetchall()
        await cursor.close()

        return [Group(*row) for row in rows]


class SubjectSevice:
    def __init__(self, db: Connection, bot: Bot | None = None):
        self.db = db
        self.bot = bot

    async def add(self, name: str):
        await self.db.execute(
            """
            INSERT OR IGNORE INTO Subjects(name) VALUES(?1)
            """,
            [name]
        )
        await self.db.commit()

    async def get_all(self) -> list[Subject]:
        cursor = await self.db.execute(
            """
            SELECT id, name FROM Subjects
            """
        )
        rows = await cursor.fetchall()
        await cursor.close()

        return [Subject(*row) for row in rows]


class UploaderSevice:
    def get_video_path(self):
        f = tempfile.NamedTemporaryFile()
        f.close()
        return f.name
