from os import getenv
from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Router, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from database import control

router = Router(name="student-bot")
bot = Bot(token=getenv("STUDENT_BOT_TOKEN"), default=DefaultBotProperties(parse_mode=ParseMode.HTML))

menuButtons = ReplyKeyboardBuilder()
menuButtons.button(text="Мої курси")
menuButtons.button(text="Змінити ім'я")
menuButtons.button(text="Мій баланс")
menuButtons.button(text="Заробити зірочки")

menuButtons.adjust(2, 1, 1)

async def setupStudentBot():
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

@router.message(CommandStart())
async def message_start_handler(message: Message):
    student = control.getStudent(message.chat.username)

    if not student:
        replyText = f"Привіт, <b>{message.chat.first_name}</b>!\nЯ RoboBot - твій помічник у навчанні. Перед тим як ми зможемо піти далі, я хотів би трохи ближче познайомимся: мне звати <b>РобоБот Робокодовіч</b>, а тебе як звати?"

        await message.answer(replyText)

@router.message(Command("menu"))
async def message_handler(message: Message):
    student = control.getStudent(username=message.chat.username)

    if student:
        await message.answer("Відкриваю для тебе меню:", reply_markup=menuButtons.as_markup())
    else:
        await message.answer("Вибач, але я поки що тебе не знаю. Давай знайомитись!\nЯ <b>РобоБот Робокодовіч</b>, а тебе як звати?.")

@router.message()
async def message_handler(message: Message):
    student = control.getStudent(message.chat.username)

    

    if not student:
        if len(message.text.split()) != 2:
            await message.answer("Вибач, але я не розумію таке ім'я. Треба написати <b>\"Призвіще Ім'я\"</b>.\"")
            return
        
        student = control.addStudent(username=message.chat.username, name=message.text.strip())
        await message.answer(f"Дякую за реєстрацію, <b>{message.chat.first_name}</> \uE022")
        await message.answer(f"Чим можу допомогти?", reply_markup=menuButtons.as_markup())
        return

    command = message.text.strip()

    match command:
        case "Мої курси":
            await message.answer(f"Мої курси")
        case "Змінити ім'я":
            await message.answer("Змінити ім'я")
        case "Мій баланс":
            await message.answer(f"У тебе є <b>{student.balance}</b> зірочок")
        case "Заробити зірочки":
            await message.answer(f"Заробити зірочоки")