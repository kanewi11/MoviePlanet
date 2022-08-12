import json
import logging
import datetime
import traceback

import asyncio

from ..config import MY_CHANNEL_URL
from .. import session, bot
from ..models import Post


async def send_post():
    """
    Функция отправки отложенных сообщений.

    :return:
    """

    while True:
        posts = session.query(Post).filter(Post.date_time <= datetime.datetime.now()).all()
        
        if not posts:
            await asyncio.sleep(20)
            continue

        for post in posts:
            json_data = json.loads(post.post)
            caption = f'🎬 <b>{json_data["title"]}</b>\n\n' \
                      f'🌎 <b>Год и страна:</b> {json_data["year_country"]}\n' \
                      f'({json_data["serial"]})\n\n' \
                      f'⭐️ {json_data["rating"]}\n\n' \
                      f'<i>{json_data["description"]}</i>\n\n' \
                      f'<b>Бот в закрепе ☝️ </b>'
            chat_id = await bot.get_chat(MY_CHANNEL_URL)
            await bot.send_photo(chat_id=chat_id.id,
                                 photo=f'https://{json_data["poster"]}',
                                 caption=caption)
            session.delete(post)

        try:
            session.commit()
            session.refresh()
        except:
            logging.warning(traceback.format_exc())
            session.rollback()
