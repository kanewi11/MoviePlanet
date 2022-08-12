import json
import traceback

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram import types

from .utils import send_films, add_user_in_db

from ..messages import msg_start, msg_help, msg_if_not_subscribed
from ..states import ForwardState, PostState, ChoiceFilmState
from .. import session, cb, dp, bot, logging
from ..keyboards import kb_cancel, kb_start, button_cancel
from ..models import Admin, Post, User
from ..config import CHANNELS_TO_SUBSCRIBE


@dp.message_handler(commands=['start'])
async def command_start(message: types.Message):
    """
    Все предельно понятно, функция обработки команды start.
    Тут высылается приветственное сообщение и кнопки для админов.

    :param message:
    :return:
    """
    text_msg = msg_start
    user = session.query(User).filter(User.user_id == str(message.from_user.id)).first()
    if not user:
        user = User(message.from_user.id)
        session.add(user)

        try:
            session.commit()
            session.refresh()
        except:
            logging.warning(traceback.format_exc())
            session.rollback()

    admin = session.query(Admin).filter(Admin.user_id == str(message.from_user.id)).first()
    if not admin:
        await bot.send_message(message.chat.id, text=text_msg.format(message.from_user.first_name))
        for group in CHANNELS_TO_SUBSCRIBE:
            user_channel_status = await bot.get_chat_member(chat_id=group, user_id=message.from_user.id)
            if user_channel_status["status"] == 'left':
                await bot.send_message(message.from_user.id, msg_if_not_subscribed)
                return
        return

    await bot.send_message(message.chat.id, text=text_msg.format(message.from_user.first_name), reply_markup=kb_start)


@dp.message_handler(commands=['help'])
async def command_help(message: types.Message):
    """
    Функция обработки команды help и отправки сообщения помощи.

    :param message:
    :return:
    """

    text_msg = msg_help

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
        text_msg = "Хммм... (ничего не найдено)"
        return await bot.send_message(message.chat.id, text=text_msg)

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
        text_msg = "Хммм... (ничего не найдено)"
        return await bot.send_message(message.chat.id, text=text_msg)

    posts = session.query(Post).all()
    if not posts:
        await message.answer('Нет отложенных постов 🫙')
        return

    for p in posts:
        kb_edit_delete = InlineKeyboardMarkup(row_width=2)
        kb_edit_delete.add(InlineKeyboardButton('Изменить ⏱', callback_data=cb.new(id=p.id, action="edit")),
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
        text_msg = "Хммм... (ничего не найдено)"
        return await bot.send_message(message.chat.id, text=text_msg)

    await message.answer('Жду пост...', reply_markup=button_cancel)
    await ForwardState.CANCEL_OR_MASSAGE.set()


@dp.message_handler(content_types=['text'])
async def send_film(message: types.Message, state: FSMContext):
    """
    Обработка запроса на поиск фильма или сериала, при первом запросе,
    последующие запросы обрабатываются в состоянии

    :param state:
    :param message:
    :return:
    """
    await add_user_in_db(user_id=message.from_user.id)
    await send_films(message=message, state=state)
    await ChoiceFilmState.first()
