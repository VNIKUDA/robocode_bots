from os import getenv
from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Router, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardRemove, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from database import control
from hashlib import sha256

storage = MemoryStorage()
router = Router(name="teacher-bot")
bot = Bot(token=getenv("TEACHER_BOT_TOKEN"), default=DefaultBotProperties(parse_mode=ParseMode.HTML))

ADMIN_PASSWORD_HASH = getenv("ADMIN_PASSWORD_HASH")

teacherMenuButtons = ReplyKeyboardBuilder()
teacherMenuButtons.button(text="Мої групи")
teacherMenuButtons.button(text="Змінити ім'я")
teacherMenuButtons.adjust(1, 1)

class GroupForm(StatesGroup):
    course = State()
    day = State()
    time = State()
    room = State()


dp = Dispatcher()
async def setupTeacherBot():
    await bot.delete_webhook()
    dp.include_router(router)
    await dp.start_polling(bot)

@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    
    await state.finish()
    await message.reply('Скасовано', reply_markup=ReplyKeyboardRemove())

@router.message(GroupForm.course)
async def course_handler(message: Message, state: FSMContext):
    await state.update_data(course=message.text)
    await state.set_state(GroupForm.day)

    await message.answer("")


@router.message(CommandStart())
async def message_start_handler(message: Message):
    teacher = control.getTeacher(message.chat.username)

    if not teacher:
        await message.answer("Привіт друже!\nХм, вперше тебе бачу, напевно новенький. Мене звати <b>РобоБот Робокодовіч</b>. А тебе як звати?")


@router.message(Command("activate_admin"))
async def message_admin_handler(message: Message):
    teacher = control.getTeacher(message.chat.username)

    if teacher:
        if len(message.text.split()) != 2:
            await message.answer("Пароль невірний.")
            return
        
        hashFromPassword = sha256(message.text.split()[-1].encode()).hexdigest()

        if hashFromPassword == ADMIN_PASSWORD_HASH:
            control.setTeacherAdminStatus(message.chat.username, True)
            await message.answer("Надаю права адміністратора та активую режим бога.\nЩо накажете робити?")
        else:
            await message.answer("Пароль невірний.")


@router.message(Command("menu"))
async def menu_start_handler(message: Message):
    teacher = control.getTeacher(message.chat.username)

    if teacher:
        await message.answer("Відкриваю меню керування:", reply_markup=teacherMenuButtons.as_markup())

@router.message()
async def message_handler(message: Message):
    teacher = control.getTeacher(message.chat.username)

    if not teacher:
        if len(message.text.split()) != 2:
            await message.answer("Ти здається щось попутав. Давай спробуєм ще раз: напиши мені <b>прізвище</b> та <b>ім'я</b>, будь-ласка.")
            return
        
        teacher = control.addTeacher(message.chat.username, message.text.strip())
        await message.answer(f"Радий тебе бачити, <b>{message.chat.first_name}</b>!\nЧим можу допомогти?")