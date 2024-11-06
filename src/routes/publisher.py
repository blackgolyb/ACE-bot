from re import Match

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from aiosqlite import Connection

from src.filters import admin_filter
from src.services.publisher import PublisherSevice

router = Router()


# @router.message(~admin_filter)
# async def handle_not_whitelisted_users(message: Message):
#     await message.answer(f"You have no acces to this bot. {message.from_user.id}")

@router.message(F.text.regexp(r"^\/map_publisher\s+(https:\/\/youtube\.com\/playlist\?list=(.+)&.+)$").as_("args"), admin_filter)
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


@router.message(F.text.regexp(r"^\/map_publisher\s*.*$"), admin_filter)
async def failed_map_publisher(message: Message) -> None:
    await message.answer("Incorrect call of map_publisher")


@router.message(Command("get_mappings"), admin_filter)
async def get_mappings(message: Message, db: Connection) -> None:
    service = PublisherSevice(db)
    data = await service.get_mappings()
    result = "\n".join(map(lambda r: f"{r[0]}: {r[1]}", data))
    if result:
        await message.answer(result, disable_web_page_preview=True)
    else:
        await message.answer("empty")
