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
from aiogram.types import Message, ReplyKeyboardRemove, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from sqlalchemy.exc import IntegrityError 

from database import control
from database.database import days
from hashlib import sha256

storage = MemoryStorage()
router = Router(name="teacher-bot")
bot = Bot(token=getenv("TEACHER_BOT_TOKEN"), default=DefaultBotProperties(parse_mode=ParseMode.HTML))

ADMIN_PASSWORD_HASH = getenv("ADMIN_PASSWORD_HASH")

teacherMenuButtons = ReplyKeyboardBuilder()
teacherMenuButtons.button(text="Мої групи")
teacherMenuButtons.button(text="Створити групу")
teacherMenuButtons.button(text="Керувати групою")
teacherMenuButtons.adjust(1, 2)

controlGroupMenuButtons = ReplyKeyboardBuilder()
controlGroupMenuButtons.button(text="Інформація про групу")
controlGroupMenuButtons.button(text="Завантажити питання")
controlGroupMenuButtons.button(text="Видалити групу")
controlGroupMenuButtons.button(text="Керувати студентами")
controlGroupMenuButtons.button(text="Вийти")
controlGroupMenuButtons.adjust(2, 2, 1)

studentControlMenuButtons = ReplyKeyboardBuilder()
studentControlMenuButtons.button(text="Інформація")
studentControlMenuButtons.button(text="Видалити з групи")
studentControlMenuButtons.button(text="Змінити баланс")
studentControlMenuButtons.button(text="Вийти")
studentControlMenuButtons.adjust(1, 2, 1)

class GroupForm(StatesGroup):
    course_category = State()
    course = State()
    day = State()
    time = State()
    room = State()

class StudentControlCallback(CallbackData, prefix="student_control"):
    student_id: int
    group_id: int

class StudentControl(StatesGroup):
    main = State()
    delete = State()
    change_balance = State()

class ControlGroupCallback(CallbackData, prefix="control_group"):
    group_id: int

class ControlGroup(StatesGroup):
    main = State()
    delete_group = State()
    upload_question = State()


dp = Dispatcher()
async def setupTeacherBot():
    await bot.delete_webhook()
    dp.include_router(router)
    await dp.start_polling(bot)


@dp.message(F.text == "Скасувати")
async def cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.reply('Скасовано', reply_markup=teacherMenuButtons.as_markup())


@dp.callback_query(StudentControlCallback.filter())
async def student_control_handler(query: CallbackQuery, callback_data: StudentControlCallback, state: FSMContext):
    teacher = control.getTeacher(query.from_user.username)
    group = control.getGroupById(callback_data.group_id)
    student = control.getStudentById(callback_data.student_id)

    if group.teacher_id != teacher.id:
        query.answer("Помилка")
        return
    
    await state.set_state(StudentControl.main)
    await state.update_data(group_id=group.id, student_id=student.id)

    balance = control.getStudentBalance(student.id, group.id)
    await query.answer(" ")
    await query.message.answer(f"Студент:\n{student.name} - {balance}", reply_markup=studentControlMenuButtons.as_markup())


@dp.message(StudentControl.main)
async def student_control_message_handler(message: Message, state: FSMContext):

    data = await state.get_data()

    student = control.getStudentById(data["student_id"])
    group = control.getGroupById(data["group_id"])
    student_balance = control.getStudentBalance(student.id, group.id)

    match message.text.strip():
        case "Інформація":
            await message.answer(f"<b>Інформація про студента</b>\nІм'я: {student.name}\nБаланс: {student_balance}")
        case "Змінити баланс":
            await state.set_state(StudentControl.change_balance)
            await message.answer(f"Поточний баланс - <b>{student_balance}</b>\nВведіть новий баланс:")
        case "Видалити з групи":
            delete_confirmation = ReplyKeyboardBuilder()
            delete_confirmation.button(text="Так")
            delete_confirmation.button(text="Ні")

            await state.set_state(StudentControl.delete)
            await message.answer(f"Видалити студента <b>{student.name}</b>?\nНапишіть \"Так\" щоб підтвердити, \"Ні\" щоб скасувати.", reply_markup=delete_confirmation.as_markup())
        case "Вийти":
            await state.set_state(ControlGroup.main)
            await message.answer("Режим керування групою", reply_markup=controlGroupMenuButtons.as_markup())


@dp.message(StudentControl.change_balance)
async def change_student_balance_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    student = control.getStudentById(data["student_id"])
    group = control.getGroupById(data["group_id"])

    new_balance = message.text.strip()

    if not new_balance.replace(".", "", 1).isnumeric():
        await message.answer("Помилка")
        return
    
    new_balance = float(new_balance)
    control.setStudentBalanceInGroup(student.id, group.id, new_balance)

    await state.set_state(StudentControl.main)
    await message.answer("Новий баланс встановлено", reply_markup=studentControlMenuButtons.as_markup())

@dp.message(StudentControl.delete)
async def delete_student_from_group_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    student = control.getStudentById(data["student_id"])
    group = control.getGroupById(data["group_id"])

    match message.text.strip():
        case "Так":
            control.leaveStudentFromGroup(student.id, group.id)

            await state.set_state(ControlGroup.main)
            await message.answer(f"Студента <b>{student.name}</b> видалено з групи.", reply_markup=controlGroupMenuButtons.as_markup())
        case "Ні":
            await state.set_state(StudentControl.main)
            await message.answer("Видалення студента скасовано.", reply_markup=studentControlMenuButtons.as_markup())


@dp.callback_query(ControlGroupCallback.filter())
async def control_group_handler(query: CallbackQuery, callback_data: ControlGroup, state: FSMContext):
    teacher = control.getTeacher(query.from_user.username)
    group = control.getGroupById(callback_data.group_id)


    if group.teacher_id != teacher.id:
        await query.answer("Помилка")

    await state.set_state(ControlGroup.main)
    await state.update_data(group_id=group.id)

    await query.answer(" ")
    await query.message.answer(f"<b>Режим керування</b>\nГрупа: {group.room} {group.day} {group.time}:00 {group.course.name}", reply_markup=controlGroupMenuButtons.as_markup())


@dp.message(ControlGroup.main)
async def control_group_message_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    group = control.getGroupById(data["group_id"])

    match message.text.strip():
        case "Видалити групу":
            await state.set_state(ControlGroup.delete_group)

            confirm_reply = ReplyKeyboardBuilder()
            confirm_reply.button(text="Так")
            confirm_reply.button(text="Ні")

            await message.answer("Видалити цю групу?\nВиберіть <b>\"Так\"</b> щоб підтвердити видалення, та <b>\"Ні\"</b> щоб скасувати видалення.", reply_markup=confirm_reply.as_markup())
        case "Інформація про групу":
            reply_text = f"<b>{group.room} {group.day} {group.time}:00 {group.course.name}</b>\n"

            if len(group.students) > 0:
                for student in group.students:
                    student_balances = control.getStudentBalances(student.id)
                    balance = [balance for balance_group, balance in student_balances if balance_group.id == group.id][0]
                    reply_text += f"{student.name} - {balance}"
            else:
                reply_text += "Студентів у групі немає."

            await message.answer(reply_text)
        case "Керувати студентами":
            if len(group.students) > 0:
                student_selection = InlineKeyboardBuilder()
                for student in group.students:
                    student_selection.button(text=student.name, callback_data=StudentControlCallback(student_id=student.id, group_id=group.id))
                
                await message.answer("Виберіть студента:", reply_markup=student_selection.as_markup())
            else:
                await message.answer("Студнетів в групі немає.")

        case "Завантажити питання":
            await state.set_state(ControlGroup.upload_question)
            await message.answer("Очікую файл питань...")

        case "Вийти":
            await state.clear()

            await message.answer("<b>Вихід з режиму керування групою</b>", reply_markup=teacherMenuButtons.as_markup())

    # await message.answer(f"{group.room} {group.day} {group.time}:00 {group.course.name}")

@dp.message(ControlGroup.upload_question)
async def upload_question_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    group = control.getGroupById(data["group_id"])

    if not message.document:
        await message.answer("Надішліть файл")
        return
    
    if message.document.file_name.split(".")[-1] != "csv":
        await message.answer("Формат файлу повинен бути CSV")
        return

    file = await message.bot.get_file(message.document.file_id)
    group_filename = f"{group.id}.csv"

    await message.bot.download_file(file.file_path, f"./media/{group_filename}")
    await message.answer("Файл успішно завантажено.")
    await state.set_state(ControlGroup.main)
    

@dp.message(ControlGroup.delete_group)
async def delete_group_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    teacher = control.getTeacher(message.chat.username)
    group = control.getGroupById(data["group_id"])

    if not group:
        await message.answer("Такої групи не існує.", reply_markup=teacherMenuButtons.as_markup())
        return
    if group.teacher_id != teacher.id:
        await message.answer("Ви не є викладачем групи.", reply_markup=teacherMenuButtons.as_markup())
        return
    
    match message.text.strip():
        case "Так":
            control.deleteGroup(group.id)

            await state.clear()
            await message.answer(f"Успішно видалено групу \"{group.room} {group.day} {group.time}:00 {group.course.name}\"", reply_markup=teacherMenuButtons.as_markup())
            return
        case "Ні":
            await state.set_state(ControlGroup.main)
            await message.answer("Видалення групи скасовано.", reply_markup=controlGroupMenuButtons.as_markup())
            return

    confirm_reply = ReplyKeyboardBuilder()
    confirm_reply.button(text="Так")
    confirm_reply.button(text="Ні")

    await message.answer("Видалити цю групу?\nВиберіть <b>\"Так\"</b> щоб підтвердити видалення, та <b>\"Ні\"</b> щоб скасувати видалення.", reply_markup=confirm_reply.as_markup())         

@dp.message(GroupForm.course_category)
async def course_category_handler(message: Message, state: FSMContext):
    course_category = control.getCourseCategory(message.text)

    if not course_category:
        await message.answer("Вибач, але такого напряму немає в базі.\nСпробуй ще раз.")
        return

    await state.update_data(course_category = course_category.id)
    await state.set_state(GroupForm.course)

    courses = control.getCoursesByCategory(course_category.id)
    course_selection = ReplyKeyboardBuilder()
    for course in courses:
        course_selection.button(text=course.name)
    course_selection.button(text="Скасувати")
    course_selection.adjust(len(courses)//2, len(courses) - len(courses) // 2, 1)

    await message.answer("До якого курсу відноситься ця група?", reply_markup=course_selection.as_markup())


@dp.message(GroupForm.course)
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
    await state.set_state(GroupForm.day)

    day_selection = ReplyKeyboardBuilder()
    for day in days:
        day_selection.button(text=day)
    day_selection.button(text="Скасувати")
    day_selection.adjust(len(days) // 2, len(days) - len(days) // 2, 1)

    await message.answer("В який день ця група займається?", reply_markup=day_selection.as_markup())


@dp.message(GroupForm.day)
async def course_handler(message: Message, state: FSMContext):
    day = message.text
    if day not in days:
        await message.answer("Вибач, але такого дня немає в базі.\nСпробуй ще раз.")
        return

    await state.update_data(day = day)
    await state.set_state(GroupForm.time)

    time_selection = ReplyKeyboardBuilder()
    for time in range(10, 20, 2):
        time_selection.button(text=str(time))
    time_selection.button(text="Скасувати")
    time_selection.adjust(5, 1)

    await message.answer("В який час ця група займається?", reply_markup=time_selection.as_markup())


@dp.message(GroupForm.time)
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
    await state.set_state(GroupForm.room)

    room_selection = ReplyKeyboardBuilder()
    for room in range(1, 4):
        room_selection.button(text=str(room))
    room_selection.button(text="Скасувати")
    room_selection.adjust(3, 1)


    await message.answer("В який аудиторії ця група займається?", reply_markup=room_selection.as_markup())


@dp.message(GroupForm.room)
async def course_handler(message: Message, state: FSMContext):
    teacher = control.getTeacher(username=message.chat.username)

    room = message.text
    if not room.isnumeric():
        await message.answer("Вибач, але це не число.\nСпробуй ще раз.")
        return
    if int(room) not in range(1, 4):
        await message.answer("Такої аудиторії не існує.\nСпробуй ще раз.")
        return

    group = await state.update_data(room = room)
    await state.clear()

    try:
        group = control.addGroup(group["day"], group["time"], group["room"], group["course"], teacher.id)

        await message.answer(f"Групу \"{group.room} {group.day} {group.time}:00 {group.course.name}\" успішно створено.", reply_markup=teacherMenuButtons.as_markup())
    except:
        await message.answer("Помилка.\nНе можна додати групу, бо аудиторія на цей час уже занята.", reply_markup=teacherMenuButtons.as_markup())


@dp.message(CommandStart())
async def message_start_handler(message: Message):
    teacher = control.getTeacher(message.chat.username)

    if not teacher:
        await message.answer("Привіт друже!\nХм, вперше тебе бачу, напевно новенький. Мене звати <b>РобоБот Робокодовіч</b>. А тебе як звати?")


@dp.message(Command("activate_admin"))
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


@dp.message(Command("execute_sql"))
async def sql_query_handler(message: Message):
    teacher = control.getTeacher(message.chat.username)

    if not teacher.isAdmin:
        await message.answer("<b>Відмова</b>\nУ вас немає прав для використання цієї команди.")
        return
    if len(message.text.split()) < 2:
        await message.answer("Помилка\nВведіть SQL запит.")
    
    try:
        result = control.executeSqlQuery(message.text.removeprefix("/execute_sql").strip())

        await message.answer(str(result), parse_mode=None)
    except Exception as e:
        await message.answer(str(e), parse_mode=None)


@dp.message(Command("execute_sqlalchemy"))
async def sql_query_handler(message: Message):
    teacher = control.getTeacher(message.chat.username)

    if not teacher.isAdmin:
        await message.answer("<b>Відмова</b>\nУ вас немає прав для використання цієї команди.")
        return
    if len(message.text.split()) < 2:
        await message.answer("Помилка\nВведіть код запиту.")    

    try:
        control.executeSqlAlchemyQuery(message.text.removeprefix("/execute_sqlalchemy").strip())

        await message.answer("Успішно", parse_mode=None)
    except Exception as e:
        await message.answer(str(e), parse_mode=None)

@dp.message(Command("evaluate_sqlalchemy"))
async def sql_query_handler(message: Message):
    teacher = control.getTeacher(message.chat.username)

    if not teacher.isAdmin:
        await message.answer("<b>Відмова</b>\nУ вас немає прав для використання цієї команди.")
        return
    if len(message.text.split()) < 2:
        await message.answer("Помилка\nВведіть код запиту.")    

    try:
        result = control.evaluateSqlAlchemyQuery(message.text.removeprefix("/evaluate_sqlalchemy").strip())

        await message.answer(str(result), parse_mode=None)
    except Exception as e:
        await message.answer(str(e), parse_mode=None)

@dp.message(Command("menu"))
async def menu_start_handler(message: Message):
    teacher = control.getTeacher(message.chat.username)

    if teacher:
        await message.answer("Відкриваю меню керування:", reply_markup=teacherMenuButtons.as_markup())

@dp.message()
async def message_handler(message: Message, state: FSMContext):
    teacher = control.getTeacher(message.chat.username)

    if not teacher:
        if len(message.text.split()) != 2:
            await message.answer("Ти здається щось попутав. Давай спробуєм ще раз: напиши мені <b>прізвище</b> та <b>ім'я</b>, будь-ласка.")
            return

        teacher = control.addTeacher(message.chat.username, message.text.strip())
        await message.answer("Приємно познайомитись)\nЧим можу допомогти?", reply_markup=teacherMenuButtons.as_markup())

    match message.text:
        case "Створити групу":
            categories = control.getAllCourseCategories()

            category_selection = ReplyKeyboardBuilder()
            for category in categories:
                category_selection.button(text=category.name)
            category_selection.button(text="Скасувати")
            category_selection.adjust(len(categories) // 2, len(categories) - len(categories) // 2, 1)

            await state.set_state(GroupForm.course_category)
            await message.answer("До якого напряму відноситься ця група?", reply_markup=category_selection.as_markup())

        case "Керувати групою":
            groups = control.getTeacherGroups(teacher.id)

            if len(groups) == 0:
                await message.answer("У тебе немає створених груп.")
                return

            group_selection = InlineKeyboardBuilder()
            for group in groups:
                group_selection.button(text=f"{group.room} {group.day} {group.time}:00 {group.course.name}", callback_data=ControlGroupCallback(group_id=group.id))
            
            await message.answer("Виберіть групу:", reply_markup=group_selection.as_markup())

        case "Мої групи":
            groups = control.getTeacherGroups(teacher.id)

            if len(groups) > 0:
                reply_text = "<b>Твої групи:</b>\n"
                for group in groups:
                    reply_text += f"{group.room} {group.day} {group.time}:00 {group.course.name}\n"
            else:
                reply_text = "У тебе немає створених груп."

            await message.answer(reply_text)
