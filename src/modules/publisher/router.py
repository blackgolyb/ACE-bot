from re import Match

from aiogram import F
from aiogram.filters import Command
from aiogram.types import Message
from aiosqlite import Connection

from src.core.routers import Router
from .services import PublisherSevice


router = Router()


@router.admin.message(F.text.regexp(r"^\/map_publisher\s+(https:\/\/youtube\.com\/playlist\?list=(.+)&.+)$").as_("args"))
async def map_publisher(message: Message, args: Match[str], db: Connection) -> None:
    try:
        await message.delete()
    except Exception as e:
        print(e)

    url = args.groups()[0]
    playlist_id = args.groups()[1]
    chat_id = message.chat.id

    service = PublisherSevice(db)
    await service.map_publisher(chat_id, playlist_id)
    await message.answer(
        f"Successfully registered this playlist for this chat\n{url}",
        disable_web_page_preview=True,
    )


@router.admin.message(F.text.regexp(r"^\/map_publisher\s*.*$"))
async def failed_map_publisher(message: Message) -> None:
    await message.answer("Incorrect call of map_publisher")


@router.admin.message(Command("get_mappings"))
async def get_mappings(message: Message, db: Connection) -> None:
    service = PublisherSevice(db)
    data = await service.get_mappings()
    result = "\n".join(map(lambda r: f"{r[0]}: {r[1]}", data))
    if result:
        await message.answer(result, disable_web_page_preview=True)
    else:
        await message.answer("empty")
