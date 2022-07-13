import json
import asyncio
import logging
import datetime
import traceback
from MoviePlanet.bot import session, bot, CHANNEL_URL
from MoviePlanet.bot.model import Post


async def send_post():
    while True:
        posts = session.query(Post).filter(Post.published == False).all()
        for post in posts:
            if post.date_time <= datetime.datetime.now():
                json_data = json.loads(post.post)
                caption = f'🎬 <b>{json_data["title"]}</b>\n\n' \
                          f'🌎 <b>Год и страна:</b> {json_data["year_country"]}\n' \
                          f'({json_data["serial"]})\n\n' \
                          f'⭐️ {json_data["rating"]}\n\n' \
                          f'<i>{json_data["description"]}</i>\n\n' \
                          f'<b>Бот в закрепе ☝️ </b>'
                chat_id = await bot.get_chat(CHANNEL_URL)
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

        await asyncio.sleep(20)
