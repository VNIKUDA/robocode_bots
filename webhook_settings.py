import asyncio
from dotenv import load_dotenv
from os import getenv

load_dotenv("/home/RoboBotServer/robocode_bots/.env") # deployed
# load_dotenv() # local dev version

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession

TEACHER_BOT_TOKEN = getenv("TEACHER_BOT_TOKEN")
STUDENT_BOT_TOKEN = getenv("STUDENT_BOT_TOKEN")
PYTHONANYWHERE_ACCOUNT = getenv("PYTHONAYNWHERE_ACCOUNT")
WEBHOOK_SECRET = getenv("WEBHOOK_SECRET")

TEACHER_WEBHOOK = "/teacher"
TEACHER_URL = f"https://{PYTHONANYWHERE_ACCOUNT}.pythonanywhere.com{TEACHER_WEBHOOK}"

STUDENT_WEBHOOK = "/student"
STUDENT_URL = f"https://{PYTHONANYWHERE_ACCOUNT}.pythonanywhere.com{STUDENT_WEBHOOK}"

async def setupWebhook():
    print("Setting webhook...")

    session = AiohttpSession(proxy="http://proxy.server:3128")

    teacher_bot = Bot(token=TEACHER_BOT_TOKEN, session=session)
    student_bot = Bot(token=STUDENT_BOT_TOKEN, session=session)

    await teacher_bot.set_webhook(TEACHER_URL, secret_token=WEBHOOK_SECRET)
    print(f"Webhook for bot with token {TEACHER_BOT_TOKEN} is {TEACHER_URL}")
    await student_bot.set_webhook(STUDENT_URL, secret_token=WEBHOOK_SECRET)
    print(f"Webhook for bot with token {STUDENT_BOT_TOKEN} is {STUDENT_URL}")

    await session.close()

async def resetWebhook():
    print("Resetting webhook...")

    teacher_bot = Bot(token=TEACHER_BOT_TOKEN)
    student_bot = Bot(token=STUDENT_BOT_TOKEN)

    await teacher_bot.delete_webhook()
    print("Teacher bot webhook was reset")
    await student_bot.delete_webhook()
    print("Student bot webhook was reset")

if __name__ == "__main__":
    asyncio.run(setupWebhook())
