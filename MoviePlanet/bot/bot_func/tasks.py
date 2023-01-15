import json
import logging
import datetime
import traceback

import asyncio

from .utils import get_caption_for_channel
from ..config import MY_CHANNEL_URL
from .. import bot, Session
from ..models import Post


async def send_post() -> None:
    """
    Функция отправки отложенных сообщений.

    :return:
    """

    while True:
        session = Session()
        posts = session.query(Post).filter(Post.date_time <= datetime.datetime.now()).all()
        
        if not posts:
            await asyncio.sleep(20)
            continue

        for post in posts:
            json_data = json.loads(post.post)
            caption = get_caption_for_channel(data=json_data)
            chat_id = await bot.get_chat(MY_CHANNEL_URL)
            await bot.send_photo(chat_id=chat_id.id, photo=f'https://{json_data["poster"]}', caption=caption)
            session.delete(post)

        try:
            session.commit()
        except:
            logging.warning(traceback.format_exc())
            session.rollback()
        finally:
            session.close()
