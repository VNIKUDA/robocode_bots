from os import getenv
from dotenv import load_dotenv

# load_dotenv("/home/RoboBotServer/robocode_bots/.env") # deployed
load_dotenv() # local dev version

from aiogram import Bot, Router, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types.callback_query import CallbackQuery
from aiogram.types import Message, PollAnswer
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from database import control
from database.database import days

import pandas as pd
import random

router = Router(name="student-bot")
storage = MemoryStorage()
bot = Bot(token=getenv("STUDENT_BOT_TOKEN"), default=DefaultBotProperties(parse_mode=ParseMode.HTML))

class EarnBalance(CallbackData, prefix="earn_balance"):
    group_id: int

class QuestionPoll(StatesGroup):
    group = State()
    question = State()

class JoinGroupForm(StatesGroup):
    course_category = State()
    course = State()
    day = State()
    time = State()
    room = State()

class LeaveGroupCallback(CallbackData, prefix="leave_group"):
    group_id: int

class LeaveGroupState(StatesGroup):
    leave = State()

menuButtons = ReplyKeyboardBuilder()
menuButtons.button(text="Мої курси")
menuButtons.button(text="Приєднатися до курсу")
menuButtons.button(text="Покинути курс")
menuButtons.button(text="Мій баланс")
menuButtons.button(text="Заробити зірочки")

menuButtons.adjust(1, 2, 2)

dp = Dispatcher()
async def setupStudentBot():
    await bot.delete_webhook()
    dp.include_router(router)
    await dp.start_polling(bot)


@dp.message(CommandStart())
async def message_start_handler(message: Message):
    student = control.getStudent(message.chat.username)

    if not student:
        replyText = f"Привіт, <b>{message.chat.first_name}</b>!\nЯ RoboBot - твій помічник у навчанні. Перед тим як ми зможемо піти далі, я хотів би трохи ближче познайомимся: мне звати <b>РобоБот Робокодовіч</b>, а тебе як звати?"

        await message.answer(replyText)


@dp.callback_query(LeaveGroupCallback.filter())
async def leave_group_handler(query: CallbackQuery, callback_data: LeaveGroupCallback, state: FSMContext):
    student = control.getStudent(query.from_user.username)
    group = control.getGroupById(callback_data.group_id)

    if not group:
        await query.answer("Помилка")
        return

    options = ReplyKeyboardBuilder()
    options.button(text="Так")
    options.button(text="Ні")

    await query.answer(" ")
    await state.set_state(LeaveGroupState.leave)
    await state.update_data(student_id=student.id, group_id=group.id)
    await query.message.answer("<b>УВАГА!!!\nПісля покидання групи баланс анулюється!</b>")
    await query.message.answer(f"Покинути групу \"{group.room} {group.day} {group.time}:00 {group.course.name}\"?", reply_markup=options.as_markup())


@dp.message(LeaveGroupState.leave)
async def leave_confirm_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    group = control.getGroupById(data["group_id"])

    match message.text.strip():
        case "Так":
            control.leaveStudentFromGroup(data["student_id"], data["group_id"])
            await message.answer(f"Ви покинули групу <b>\"{group.room} {group.day} {group.time}:00 {group.course.name}\"</b>.", reply_markup=menuButtons.as_markup())
        case "Ні":
            await message.answer(f"Покидання групи <b>\"{group.room} {group.day} {group.time}:00 {group.course.name}\"</b> скасовано.", reply_markup=menuButtons.as_markup())
    await state.clear()


@dp.message(F.text == "Скасувати")
async def cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.reply('Скасовано', reply_markup=menuButtons.as_markup())


@dp.callback_query(EarnBalance.filter())
async def earn_balance_handler(query: CallbackQuery, callback_data: EarnBalance, state: FSMContext):
    student = control.getStudent(query.from_user.username)
    group = control.getGroupById(callback_data.group_id)
    has_answered = control.getStudentQuizCompletetion(student.id, group.id)

    if not group:
        return
    if has_answered:
        await query.answer("Помилка")
        await query.message.answer("Вибач, але це можна робити тільки один раз на день.\nПовертайся завтра щоб заробити ще зірочок!")
        return
    
    try:
        filename = f"./media/{group.id}.csv"
        questions = pd.read_csv(filename)
    except FileNotFoundError:
        await query.answer(" ")
        await query.message.answer("Поки що немає доступних питань. Зверніться до вчителя.")
        return

    question = questions.iloc[random.randint(0, len(questions) - 1)]

    await query.answer(" ")
    await state.set_state(QuestionPoll.question)
    await state.update_data(correct_option_id=question["correct_option_id"], group_id=group.id, student_id=student.id)
    await query.message.answer_poll(
        question=question["question"], 
        options=[str(question[f"option{num}"]) for num in range(1, 5) if question[f"option{num}"] != ""],
        correct_option_id=question["correct_option_id"],
        type="quiz",
        is_anonymous=False
    )


@dp.poll_answer(QuestionPoll.question)
async def poll_answer_handler(answer: PollAnswer, bot: Bot, state: FSMContext): 
    data = await state.get_data()
    
    control.setStudentQuizCompletion(data["student_id"], data["group_id"])

    if answer.option_ids[0] == data["correct_option_id"]:
        balance = control.getStudentBalance(data["student_id"], data["group_id"])
        control.setStudentBalanceInGroup(data["student_id"], data["group_id"], balance + 0.5)
        await bot.send_message(answer.user.id, "<b>Правильна віпдовідь</b>\nМолодець! Твій баланс збільшено на 0.5.")
    else:
        await bot.send_message(answer.user.id, "<b>Неправильна відповідь</b>\nНе засмучуйся! Завтра можна буде повторити спробу :)")

    await state.clear()


@dp.message(JoinGroupForm.course_category)
async def course_category_handler(message: Message, state: FSMContext):
    course_category = control.getCourseCategory(message.text)

    if not course_category:
        await message.answer("Вибач, але такого напряму немає в базі.\nСпробуй ще раз.")
        return

    await state.update_data(course_category = course_category.id)
    await state.set_state(JoinGroupForm.course)

    courses = control.getCoursesByCategory(course_category.id)
    course_selection = ReplyKeyboardBuilder()
    for course in courses:
        course_selection.button(text=course.name)
    course_selection.button(text="Скасувати")
    course_selection.adjust(len(courses)//2, len(courses) - len(courses) // 2, 1)

    await message.answer("Який курс?", reply_markup=course_selection.as_markup())


@dp.message(JoinGroupForm.course)
async def course_handler(message: Message, state: FSMContext):
    course = control.getCourse(message.text)

    state_data = await state.get_data()

    if not course:
        await message.answer("Вибач, але такого курсу немає в базі.\nСпробуй ще раз.")
        return
    
    if course.course_category_id != state_data["course_category"]:
        await message.answer("Вибач, але цей курс не належить поточному напрямку.\nСпробуй ще раз.")
        return

    await state.update_data(course = course.id)
    await state.set_state(JoinGroupForm.day)

    day_selection = ReplyKeyboardBuilder()
    for day in days:
        day_selection.button(text=day)
    day_selection.button(text="Скасувати")
    day_selection.adjust(len(days) // 2, len(days) - len(days) // 2, 1)

    await message.answer("В який день ця група займається?", reply_markup=day_selection.as_markup())


@dp.message(JoinGroupForm.day)
async def course_handler(message: Message, state: FSMContext):
    day = message.text
    if day not in days:
        await message.answer("Вибач, але такого дня немає в базі.\nСпробуй ще раз.")
        return

    await state.update_data(day = day)
    await state.set_state(JoinGroupForm.time)

    time_selection = ReplyKeyboardBuilder()
    for time in range(10, 20, 2):
        time_selection.button(text=str(time))
    time_selection.button(text="Скасувати")
    time_selection.adjust(5, 1)

    await message.answer("В який час ця група займається?", reply_markup=time_selection.as_markup())


@dp.message(JoinGroupForm.time)
async def course_handler(message: Message, state: FSMContext):
    time = message.text
    if not time.isnumeric():
        await message.answer("Вибач, але це не число.\nСпробуй ще раз.")
        return
    
    time = int(time)
    if time not in range(0, 25):
        await message.answer("Вибач, але такого часу не може бути.\nСробуй ще раз.")
        return

    await state.update_data(time = time)
    await state.set_state(JoinGroupForm.room)

    room_selection = ReplyKeyboardBuilder()
    for room in range(1, 4):
        room_selection.button(text=str(room))
    room_selection.button(text="Скасувати")
    room_selection.adjust(3, 1)

    await message.answer("В який аудиторії ця група займається?", reply_markup=room_selection.as_markup())


@dp.message(JoinGroupForm.room)
async def course_handler(message: Message, state: FSMContext):
    student = control.getStudent(username=message.chat.username)

    room = message.text
    if not room.isnumeric():
        await message.answer("Вибач, але це не число.\nСпробуй ще раз.")
        return

    group = await state.update_data(room = room)
    await state.clear()

    group = control.getGroup(group["day"], group
    ["time"], group["room"], group["course"])
    if not group:
        await message.answer("Нажаль такої групи не існує.", reply_markup=menuButtons.as_markup())
        return
    control.joinStudentToGroup(student.id, group.id)

    await message.answer(f"Тебе успішно додано до групи \"{group.room} {group.day} {group.time}:00 {group.course.name}\".", reply_markup=menuButtons.as_markup())


@dp.message(Command("menu"))
async def message_handler(message: Message):
    student = control.getStudent(username=message.chat.username)

    if student:
        await message.answer("Відкриваю для тебе меню:", reply_markup=menuButtons.as_markup())
    else:
        await message.answer("Вибач, але я поки що тебе не знаю. Давай знайомитись!\nЯ <b>РобоБот Робокодовіч</b>, а тебе як звати?.")


@dp.message()
async def message_handler(message: Message, state: FSMContext):
    student = control.getStudent(message.chat.username)

    if not student:
        if len(message.text.split()) != 2:
            await message.answer("Вибач, але я не розумію таке ім'я. Треба написати <b>\"Призвіще Ім'я\"</b>.\"")
            return

        student = control.addStudent(username=message.chat.username, name=message.text.strip())
        await message.answer("Приємно познайомитись)\Чим можу допомогти?", reply_markup=menuButtons.as_markup())
        return

    command = message.text.strip()
    groups = control.getStudentGroups(message.chat.username)

    match command:
        case "Мої курси":            
            if len(groups) == 0:
                await message.answer("У тебе немає приєднаних курсів.")
                return

            reply_text = "<b>Мої курси:</b>\n"
            for group in groups:
                reply_text += f"{group.room} {group.day} {group.time}:00 {group.course.name}\n"

            await message.answer(reply_text)

        case "Приєднатися до курсу":
            categories = control.getAllCourseCategories()

            category_selection = ReplyKeyboardBuilder()
            for category in categories:
                category_selection.button(text=category.name)
            category_selection.button(text="Скасувати")
            category_selection.adjust(len(categories) // 2, len(categories) - len(categories) // 2, 1)

            await state.set_state(JoinGroupForm.course_category)
            await message.answer("Який напрям курс?", reply_markup=category_selection.as_markup())

        case "Покинути курс":
            groups_to_delete = InlineKeyboardBuilder()
            for group in groups:
                groups_to_delete.button(
                    text=f"{group.room} {group.day} {group.time}:00 {group.course.name}",
                    callback_data=LeaveGroupCallback(group_id=group.id)
                )
            await message.answer("Виберіть групу:", reply_markup=groups_to_delete.as_markup())

        case "Мій баланс":
            student_balances = control.getStudentBalances(student.id)

            reply_text = "Твій баланс:\n"
            for group, balance in student_balances:
                reply_text += f"{group.room} {group.day} {group.time} {group.course.name} - {balance}\n"

            await message.answer(reply_text)
            
        case "Заробити зірочки":
            group_selection = InlineKeyboardBuilder()
            for group in groups:
                group_selection.button(
                    text=f"{group.room} {group.day} {group.time}:00 {group.course.name}",
                    callback_data=EarnBalance(group_id=group.id)
                )

            await message.answer("Виберіть курс:", reply_markup=group_selection.as_markup())