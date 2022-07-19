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
from .states import ForwardState, PostState, EditPostState
from .search_film import make_post, find_film
from .models import User, Admin, Post
from .keyboards import *
from .config import *


logging.basicConfig(filename="logs.log", level=logging.INFO)

engine = create_engine('sqlite:///base.db', echo=False)
Session = sessionmaker(bind=engine)
session = Session()

cb = CallbackData("post", "id", "action")

bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())


from .bot_func import *


async def on_bot_start_up(dispatcher: Dispatcher):
    asyncio.create_task(send_post())


async def on_shutdown(disp):
    logging.warning('Shutting down..')
    await bot.delete_webhook()

    await disp.storage.close()
    await disp.storage.wait_closed()

    logging.warning('Bye!')


def start_bot():
    executor.start_polling(dp, skip_updates=True, on_startup=on_bot_start_up)
