import asyncio
import sys

from aiogram import Dispatcher

from bots import studentBot, teacherBot
from database.database import setupDatabase

setupDatabase()

async def main():
    studentBotTask = asyncio.create_task(studentBot.setupStudentBot())
    teacherBotTask = asyncio.create_task(teacherBot.setupTeacherBot())

    await studentBotTask
    await teacherBotTask

if __name__ == "__main__":
    print("Server is running...")
    asyncio.run(main())