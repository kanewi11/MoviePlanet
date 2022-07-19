import json
import traceback
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram import types
from ..states import ForwardState, PostState
from ..models import User, Admin, Post
from ..search_film import find_film
from .. import session, cb, dp, bot, logging
from ..keyboards import *
from ..msg_text import *
from ..config import *


@dp.message_handler(commands=['start'])
async def command_start(message: types.Message):
    """
    Все предельно понятно, функция обработки команды start.
    Тут высылается приветственное сообщение и кнопки для админов.

    :param message:
    :return:
    """

    if message.chat.type == "private":
        text_msg = msg_start
    else:
        text_msg = "Этот бот не предназначен для использования в общих чатах."

    r = User(message.from_user.id)
    session.add(r)

    try:
        session.commit()
        session.refresh()
    except:
        logging.warning(traceback.format_exc())
        session.rollback()

    admin = session.query(Admin).filter(Admin.user_id == str(message.from_user.id)).first()
    if not admin:
        await bot.send_message(message.chat.id, text=text_msg)
        return

    await bot.send_message(message.chat.id, text=text_msg, reply_markup=kb_start)


@dp.message_handler(commands=['help'])
async def command_help(message: types.Message):
    """
    Функция обработки команды help и отправки сообщения помощи.

    :param message:
    :return:
    """

    text_msg = text_help

    await bot.send_message(message.chat.id, text=text_msg)


@dp.message_handler(text="Сделать пост фильма 🤳")
async def post(message: types.Message):
    """
    Функция перенаправления на машину состояния для создания поста в группе.

    :param message:
    :return:
    """

    admin = session.query(Admin).filter(Admin.user_id == str(message.from_user.id)).first()

    if not admin:
        return

    await message.answer("🏁 Итак, приступим.\n\n🔗 Вышлите ссылку на фильм или сериал!", reply_markup=kb_cancel)
    await PostState.first()


@dp.message_handler(text="Отложенные посты 🕜")
async def deferred_post(message: types.Message):
    """
    Функция просмотра отложенных постов.

    :param message:
    :return:
    """

    admin = session.query(Admin).filter(Admin.user_id == str(message.from_user.id)).first()

    if not admin:
        return

    posts = session.query(Post).all()
    if not posts:
        await message.answer('Нет отложенных постов 🫙')
        return

    for p in posts:
        kb_edit_delete = InlineKeyboardMarkup(row_width=2)
        kb_edit_delete.add(
            InlineKeyboardButton('Изменить ⏱', callback_data=cb.new(id=p.id, action="edit")),
            InlineKeyboardButton('Удалить ❌', callback_data=cb.new(id=p.id, action="delete")))
        json_data = json.loads(p.post)
        caption = f'🎬 <b>{json_data["title"]}</b>\n\n' \
                  f'🌎 <b>Год и страна:</b> {json_data["year_country"]}\n' \
                  f'({json_data["serial"]})\n\n' \
                  f'⭐️ {json_data["rating"]}\n\n' \
                  f'<i>{json_data["description"]}</i>\n\n' \
                  f'<b>Бот в закрепе ☝️ </b>\n\n' \
                  f'Дата и время публикации: <b>{p.date_time.strftime("%d.%m.%Y %H:%M")}</b>'
        await bot.send_photo(chat_id=message.from_user.id,
                             photo=f'https://{json_data["poster"]}',
                             caption=caption, reply_markup=kb_edit_delete)


@dp.message_handler(text="Рекламный пост 💰")
async def wait_forward(message: types.Message, state: FSMContext):
    """
    Функция для отправки рекламного поста (не полностью дописана из-за ненадобности)

    :param message:
    :param state:
    :return:
    """
    admin = session.query(Admin).filter(Admin.user_id == str(message.from_user.id)).first()

    if not admin:
        return

    await message.answer('Жду пост...', reply_markup=button_cancel)
    await ForwardState.cancel_or_message.set()


@dp.message_handler()
async def main(message: types.Message):
    """
    Обработка запроса на поиск фильма или сериала.

    В плане переписать функцию и сделать вывод постранично, а так же обдумать кэширование.

    :param message:
    :return:
    """

    if message.chat.type != "private":
        text_msg = "Этот бот не предназначен для использования в общих чатах."
        return await bot.send_message(message.chat.id, text=text_msg)

    if message.text.startswith('/'):
        text_msg = "Хммм...\nТакой команды не припомню 🤔"
        return await bot.send_message(message.chat.id, text=text_msg)

    for group in CHANNELS_TO_SUBSCRIBE:
        user_channel_status = await bot.get_chat_member(chat_id=group, user_id=message.from_user.id)
        if user_channel_status["status"] != 'left':
            pass
        else:
            await bot.send_message(message.from_user.id, msg_if_not_subscribed)
            return

    await bot.send_message(message.chat.id, text='🔎 Ищу...\nПоиск может занять до 15 секунд.')
    films = await find_film(message.text)

    if not films:
        text_msg = "По вашему запросу ничего не найдено 😕"
        return await bot.send_message(message.chat.id, text=text_msg)

    for film in films:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="📺 Смотреть",
                                                url=f'{SITE_URL}/?q=' +
                                                    film['player']['iframe_url']
                                                    + '?d=movielab.top'))
        serial = str()
        if film['type'] == 'serial':
            serial = '\n<b>(Сериал)</b>'
        caption = f'<b>📽 {film["title_ru"]}</b>{serial}\n\n' \
                  f'<b>Озвучка</b>: {film["player"]["translator"]}\n\n ' \
                  f'⭐ {film["rating"]}'
        await bot.send_photo(message.chat.id,
                             photo=f'https://{film["poster"].replace("//", "").replace("170-233", "680-1000")}',
                             caption=caption,
                             reply_markup=keyboard)
