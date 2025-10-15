import asyncio
from os import getenv
from dotenv import load_dotenv

load_dotenv("/home/RoboBotServer/robocode_bots/.env")

from flask import Flask, request

from database.database import setupDatabase
from bots import teacherBot, studentBot
# from webhook_settings import setupWebhook

from aiogram import Bot
from aiogram.types import Update
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Teacher bot settings
TEACHER_BOT_TOKEN = getenv("TEACHER_BOT_TOKEN")
TEACHER_WEBPATH = "/teacher"

# Student bot settings
STUDENT_BOT_TOKEN = getenv("STUDENT_BOT_TOKEN")
STUDENT_WEBPATH = "/student"

SECRET_TOKEN = getenv("WEBHOOK_SECRET")

setupDatabase()
# setupWebhook()
application = Flask(__name__)

@application.route(TEACHER_WEBPATH, methods=["POST"])
def teacher_bot_request_handler():
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != SECRET_TOKEN:
        return 'Forbidden', 403

    update_json = request.json

    async def teacher_bot_handler():
        async with AiohttpSession("http://proxy.server:3128") as session:
            bot = Bot(token=TEACHER_BOT_TOKEN, session=session, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
            update = Update.model_validate(update_json, context={"bot": bot})

            await teacherBot.dp.feed_update(bot, update)

    asyncio.run(teacher_bot_handler())
    return "OK", 200

@application.route(STUDENT_WEBPATH, methods=["POST"])
def student_bot_request_handler():
    if request.headers.get("X-Telegram-Bot_api-Secret-Token") != SECRET_TOKEN:
        return "Forbidden", 403

    update_json = request.json

    async def student_bot_handler():
        async with AiohttpSession("http://proxy.server:3128") as session:
            bot = Bot(token=STUDENT_BOT_TOKEN, session=session, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
            update = Update.model_validate(update_json, context={"bot": bot})

            await studentBot.dp.feed_update(bot, update)


    asyncio.run(student_bot_handler())
    return "OK", 200
