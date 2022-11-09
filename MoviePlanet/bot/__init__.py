import asyncio
import logging

from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.callback_data import CallbackData
from aiogram.dispatcher import Dispatcher
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from aiogram.utils import executor
from aiogram import Bot, types

from .config import API_TOKEN

logging.basicConfig(level=logging.INFO, filename='logs.log', format='%(asctime)s %(levelname)s %(message)s')

engine = create_engine('sqlite:///base.db', echo=False)
Session = sessionmaker(bind=engine)
session = Session()

cb = CallbackData('post', 'id', 'action')

bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

WEBHOOK_HOST = 'https://kingzmsk.ru'
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

WEBAPP_HOST = 'localhost'
WEBAPP_PORT = 3001

from .bot_func import *


async def on_bot_start_up(dispatcher: Dispatcher):
    asyncio.create_task(send_post())


async def on_startup(dispatcher: Dispatcher):
    await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(dispatcher: Dispatcher):
    logging.warning('Shutting down..')

    await bot.delete_webhook()

    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()

    logging.warning('Bye!')


def start_bot():
    executor.start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
