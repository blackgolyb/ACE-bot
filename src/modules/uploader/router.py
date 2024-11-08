import datetime

from aiogram import F, Bot
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State, any_state
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiosqlite import Connection

from .service import GroupSevice, SubjectSevice, UploaderSevice, LessonVideo, LessonTypeEnum
from src.core.routers import Router


router = Router()


class UploadVideoForm(StatesGroup):
    date = State()
    group = State()
    subject = State()
    type = State()
    order = State()
    finish = State()


order_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Була тільки одна пара", callback_data="None")],
    [InlineKeyboardButton(text="Перша пара", callback_data="1")],
    [InlineKeyboardButton(text="Друга Пара", callback_data="2")],
    [InlineKeyboardButton(text="Третя Пара", callback_data="3")],
])

lesson_type_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Лекція", callback_data="1")],
    [InlineKeyboardButton(text="Практика", callback_data="2")],
    [InlineKeyboardButton(text="Семінар", callback_data="3")],
])


@router.admin.message(Command("add_group"))
async def add_group(message: Message, command: CommandObject, db: Connection) -> None:
    service = GroupSevice(db=db)
    if command.args is None:
        await message.answer("Команда повинна приймати одни параметн це дисципліну")
        return
    group = command.args.strip()
    await service.add(group)
    await message.answer(f"Додано групу: {group}")


@router.admin.message(Command("add_subject"))
async def add_subject(message: Message, command: CommandObject, db: Connection) -> None:
    service = SubjectSevice(db=db)
    if command.args is None:
        await message.answer("Команда повинна приймати одни параметн це группу")
        return
    subject = command.args.strip()
    await service.add(subject)
    await message.answer(f"Додано дисципліну: {subject}")


@router.admin.message(Command("get_all_groups"))
async def get_all_groups(message: Message, db: Connection) -> None:
    service = GroupSevice(db=db)
    groups = await service.get_all()
    if not groups:
        await message.answer("empty")
        return
    await message.answer("\n".join(map(str, groups)))


@router.admin.message(Command("get_all_subjects"))
async def get_all_subjects(message: Message, db: Connection) -> None:
    service = SubjectSevice(db=db)
    subjects = await service.get_all()
    if not subjects:
        await message.answer("empty")
        return
    await message.answer("\n".join(map(str, subjects)))


async def create_groups_keyboard(service: GroupSevice):
    groups = await service.get_all()
    buttons = [
        [InlineKeyboardButton(text=group.name, callback_data=str(group.id))]
        for group in groups
    ]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Без групи", callback_data="None")],
        *buttons,
    ])


async def create_subjects_keyboard(service: SubjectSevice):
    subjects = await service.get_all()
    buttons = [
        [InlineKeyboardButton(text=subject.name, callback_data=str(subject.id))]
        for subject in subjects
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.admin.message(Command("cancel"), any_state)
async def cancel_form(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Форма відмінена")


@router.admin.message(Command("upload_video"))
async def start_upload_videos(message: Message, state: FSMContext) -> None:
    await state.set_state(UploadVideoForm.date)
    await message.answer("Напишіть дату формата dd.mm.yyyy")


@router.admin.message(UploadVideoForm.date)
async def set_date(message: Message, state: FSMContext, db: Connection) -> None:
    try:
        date = datetime.datetime.strptime(message.text, '%d.%m.%Y').date()
    except ValueError:
        await message.answer("Напишіть дату правильно в форматі dd.mm.yyyy")
        return

    await state.update_data(date=date)
    await state.set_state(UploadVideoForm.group)

    service = GroupSevice(db=db)
    keyboard = await create_groups_keyboard(service)
    await message.answer("Оберіть групу", reply_markup=keyboard)


@router.admin.callback_query(UploadVideoForm.group)
async def set_group(callback: CallbackQuery, state: FSMContext, bot: Bot, db: Connection) -> None:
    group = None
    if callback.data != "None":
        group = int(callback.data)
    await state.update_data(group=group)
    await state.set_state(UploadVideoForm.subject)
    await callback.answer()

    service = SubjectSevice(db=db)
    keyboard = await create_subjects_keyboard(service)
    await callback.message.answer("Оберіть дисципліну", reply_markup=keyboard)


@router.admin.callback_query(UploadVideoForm.subject)
async def set_subject(callback: CallbackQuery, state: FSMContext, bot: Bot, db: Connection) -> None:
    subject = int(callback.data)
    await state.update_data(subject=subject)
    await state.set_state(UploadVideoForm.type)
    await callback.answer()
    await callback.message.answer("Оберіть тип пати", reply_markup=lesson_type_keyboard)


@router.admin.callback_query(UploadVideoForm.type)
async def set_type(callback: CallbackQuery, state: FSMContext, bot: Bot, db: Connection) -> None:
    lesson_type = LessonTypeEnum(int(callback.data))
    await state.update_data(type=lesson_type)
    await state.set_state(UploadVideoForm.order)
    await callback.answer()
    await callback.message.answer("Оберіть порякод пари", reply_markup=order_keyboard)


@router.admin.callback_query(UploadVideoForm.order)
async def set_order(callback: CallbackQuery, state: FSMContext, bot: Bot, db: Connection) -> None:
    order = None
    if callback.data != "None":
        order = int(callback.data)

    await state.update_data(order=order)
    await state.set_state(UploadVideoForm.finish)
    await callback.answer()
    await callback.message.answer("Завантажте відео")


@router.admin.message(UploadVideoForm.finish, F.video)
async def finish_upload_video_form(message: Message, state: FSMContext, bot: Bot, db: Connection) -> None:
    data = await state.get_data()
    service = UploaderSevice()
    video_path = service.get_video_path()
    print(data)
    print(video_path)
    # await bot.download(message.video, destination=video_path)
    # TODO: use this https://github.com/aiogram/aiogram/discussions/557 to load large files
    await state.clear()
    await message.answer("Відео завантажено")

@router.admin.message(UploadVideoForm.finish)
async def finish_upload_video_form_failed(message: Message, state: FSMContext, bot: Bot, db: Connection) -> None:
    await message.answer("Надішліть відео")
