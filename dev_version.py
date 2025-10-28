import asyncio
import sys

from aiogram import Dispatcher

from bots import studentBot, teacherBot
from database.database import setupDatabase
from database.control import resetStudentsQuizCompletion
from webhook_settings import resetWebhook
from apscheduler.schedulers.asyncio import AsyncIOScheduler

setupDatabase()

async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(resetStudentsQuizCompletion, trigger="cron", year="*", month="*", day="*", hour="*", minute="*", second=30)
    scheduler.start()

    studentBotTask = asyncio.create_task(studentBot.setupStudentBot())
    teacherBotTask = asyncio.create_task(teacherBot.setupTeacherBot())

    await studentBotTask
    await teacherBotTask

if __name__ == "__main__":
    asyncio.run(resetWebhook())
    print("Server is running...")
    asyncio.run(main())