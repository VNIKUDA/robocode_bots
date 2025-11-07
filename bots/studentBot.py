from os import getenv
from dotenv import load_dotenv

load_dotenv("/home/RoboBotServer/robocode_bots/.env") # deployed
# load_dotenv() # local dev version

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

storage = MemoryStorage()
bot = Bot(token=getenv("STUDENT_BOT_TOKEN"), default=DefaultBotProperties(parse_mode=ParseMode.HTML))

class EarnBalance(CallbackData, prefix="earn_balance"):
    group_id: int

class QuestionPoll(StatesGroup):
    group = State()
    question = State()

class JoinGroup(StatesGroup):
    group_code = State()
    login = State()

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

cancelButton = ReplyKeyboardBuilder()
cancelButton.button(text="Скасувати")


dp = Dispatcher()
async def setupStudentBot():
    await bot.delete_webhook()
    await dp.start_polling(bot)


@dp.message(CommandStart())
async def message_start_handler(message: Message):
    student = control.getStudent(message.chat.username)

    if not student:
        control.addStudent(message.chat.username)
        await message.answer("Приємно познайомитись)\nЧим можу допомогти?", reply_markup=menuButtons.as_markup())


@dp.callback_query(LeaveGroupCallback.filter())
async def leave_group_handler(query: CallbackQuery, callback_data: LeaveGroupCallback, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        return

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
    await query.message.edit_reply_markup(reply_markup=None)
    await query.message.answer(f"Покинути групу \"{group.room} {group.day} {group.time}:00 {group.course.name}\"?", reply_markup=options.as_markup())


@dp.message(LeaveGroupState.leave)
async def leave_confirm_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    student = control.getStudent(message.chat.username)
    group = control.getGroupById(data["group_id"])

    match message.text.strip():
        case "Так":
            control.deloginGroupStudent(student.id, group.id)
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
    await message.answer('Скасовано', reply_markup=menuButtons.as_markup())


@dp.callback_query(EarnBalance.filter())
async def earn_balance_handler(query: CallbackQuery, callback_data: EarnBalance, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        return

    student = control.getStudent(query.from_user.username)
    group = control.getGroupById(callback_data.group_id)
    has_answered = control.getStudentQuizCompletetion(student.id, group.id)

    if not group:
        return
    if has_answered:
        await query.answer("Помилка")
        await query.message.edit_text("Вибач, але це можна робити тільки один раз на день.\nПовертайся завтра щоб заробити ще зірочок!", reply_markup=None)
        return

    try:
        filename = f"./media/{group.id}.csv"
        questions = pd.read_csv(filename)
    except FileNotFoundError:
        await query.answer(" ")
        await query.message.edit_reply_markup(reply_markup=None)
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
    group_student = control.getGroupStudent(data["student_id"], data["group_id"])

    if answer.option_ids[0] == data["correct_option_id"]:
        control.setGroupStudentBalance(group_student.id, group_student.balance + 0.5)
        await bot.send_message(answer.user.id, "<b>Правильна віпдовідь</b>\nМолодець! Твій баланс збільшено на 0.5.")
    else:
        await bot.send_message(answer.user.id, "<b>Неправильна відповідь</b>\nНе засмучуйся! Завтра можна буде повторити спробу :)")

    await state.clear()


@dp.message(JoinGroup.group_code)
async def join_group_code_handler(message: Message, state: FSMContext):
    code = message.text.strip()
    group = control.getGroupByCode(code)

    if not group:
        await message.answer("Групи з таким кодом доступа не існує.", reply_markup=menuButtons.as_markup())
        return

    await state.update_data(group_id=group.id)
    await state.set_state(JoinGroup.login)
    await message.answer("Введіть ваш логін:", reply_markup=cancelButton.as_markup())


@dp.message(JoinGroup.login)
async def login_group_code_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    login = message.text.strip()
    group_student = control.getGroupStudentByLogin(login, data["group_id"])

    if not group_student:
        await message.answer("Помилка\nСтудента з таким логіном не існує.", reply_markup=cancelButton.as_markup())
        return

    group = group_student.group
    student = control.getStudent(message.chat.username)
    if group_student.student_id == student.id:
        await message.answer("Помилка\nВи вже авторизовані.", reply_markup=menuButtons.as_markup())
        await state.clear()
        return

    if group_student.student_id is not None:
        await message.answer("Помилка\nСтудента вже авторизовано на іншому телеграм акаунті.", reply_markup=menuButtons.as_markup())
        await state.clear()
        return

    control.loginGroupStudent(login, student.id, group.id)

    await state.clear()
    await message.answer(f"Вітаю, <b>{group_student.student_name}</b>\nТебе авторизовано в групі <b>{group.room} {group.day} {group.time}:00 {group.course.name}</b>", reply_markup=menuButtons.as_markup())


@dp.message(Command("menu"))
async def message_handler(message: Message):
    student = control.getStudent(username=message.chat.username)

    if not student:
        return

    await message.answer("Відкриваю меню:", reply_markup=menuButtons.as_markup())


@dp.message()
async def message_handler(message: Message, state: FSMContext):
    student = control.getStudent(message.chat.username)

    if not student:
        return

    command = message.text.strip()
    groups = control.getStudentGroupsById(student.id)

    match command:
        case "Мої курси":
            if len(groups) == 0:
                await message.answer("У тебе немає приєднаних курсів.")
                return

            reply_text = "<b>Мої курси:</b>\n"
            for group in groups:
                reply_text += f" ● {group.room} {group.day} {group.time}:00 {group.course.name}\n"

            await message.answer(reply_text)

        case "Приєднатися до курсу":
            await state.set_state(JoinGroup.group_code)
            await message.answer("Введіть код групи", reply_markup=cancelButton.as_markup())

        case "Покинути курс":
            if len(groups) == 0:
                await message.answer("У тебе немає приєднаних курсів.")
                return

            groups_to_delete = InlineKeyboardBuilder()

            for group in groups:
                groups_to_delete.button(
                    text=f"{group.room} {group.day} {group.time}:00 {group.course.name}",
                    callback_data=LeaveGroupCallback(group_id=group.id)
                )
            groups_to_delete.adjust(*[1 for _ in range(len(groups))])
            await message.answer("Виберіть групу:", reply_markup=groups_to_delete.as_markup())

        case "Мій баланс":
            student_balances = control.getStudentBalances(student.id)

            if len(student_balances) == 0:
                await message.answer("У тебе немає приєднаних курсів.")
                return

            reply_text = "Твій баланс:\n"
            for group, balance in student_balances:
                reply_text += f"{group.room} {group.day} {group.time} {group.course.name} - {balance}\n"

            await message.answer(reply_text)

        case "Заробити зірочки":
            if len(groups) == 0:
                await message.answer("У тебе немає приєднаних курсів.")
                return

            group_selection = InlineKeyboardBuilder()

            for group in groups:
                group_selection.button(
                    text=f"{group.room} {group.day} {group.time}:00 {group.course.name}",
                    callback_data=EarnBalance(group_id=group.id)
                )
            group_selection.adjust(*[1 for _ in range(len(groups))])

            await message.answer("Виберіть курс:", reply_markup=group_selection.as_markup())