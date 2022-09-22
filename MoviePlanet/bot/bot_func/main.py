import json

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram import types

from .decorators import only_admin
from .utils import send_films, add_user_in_db, get_caption_for_channel, admin_keyboard
from .states_group import ForwardState, PostState, ChoiceFilmState
from ..messages import msg_start, msg_help
from .. import session, cb, dp, bot
from ..keyboards import kb_cancel, button_cancel
from ..models import Post


@dp.message_handler(commands=['start'])
async def command_start(message: types.Message):
    """Функция обработки команды start. Тут высылается приветственное сообщение и кнопки для админа."""

    await add_user_in_db(user_id=message.from_user.id)
    await bot.send_message(message.chat.id, text=msg_start.format(message.from_user.first_name))
    await admin_keyboard(message=message)


@dp.message_handler(commands=['help'])
async def command_help(message: types.Message):
    """Функция обработки команды help и отправки сообщения помощи"""

    text_msg = msg_help

    await bot.send_message(message.chat.id, text=text_msg)


@only_admin
@dp.message_handler(text='Сделать пост фильма 🤳')
async def make_post(message: types.Message):
    """Функция перенаправления на машину состояния для создания поста в группе"""
    await message.answer("🏁 Итак, приступим.\n\n🔗 Вышлите ссылку на фильм или сериал!", reply_markup=kb_cancel)
    await PostState.first()


@only_admin
@dp.message_handler(text='Отложенные посты 🕜')
async def deferred_post(message: types.Message):
    """Функция просмотра отложенных постов"""

    posts = session.query(Post).all()
    if not posts:
        await message.answer('Нет отложенных постов 🫙')
        return

    for post in posts:
        kb_edit_delete = InlineKeyboardMarkup(row_width=2)
        kb_edit_delete.add(InlineKeyboardButton('Изменить ⏱', callback_data=cb.new(id=post.id, action="edit")),
                           InlineKeyboardButton('Удалить ❌', callback_data=cb.new(id=post.id, action="delete")))

        json_data = json.loads(post.post)
        caption = await get_caption_for_channel(data=json_data)
        caption += f'\n\nДата и время публикации: <b>{post.date_time.strftime("%d.%m.%Y %H:%M")}</b>'
        await bot.send_photo(chat_id=message.from_user.id,
                             photo=f'https://{json_data["poster"]}',
                             caption=caption, reply_markup=kb_edit_delete)


@only_admin
@dp.message_handler(text='Рекламный пост 💰')
async def wait_forward(message: types.Message):
    """Функция для отправки рекламного поста (не полностью дописана из-за ненадобности)"""
    await message.answer('Жду пост...', reply_markup=button_cancel)
    await ForwardState.CANCEL_OR_MASSAGE.set()


@dp.message_handler(content_types=['text'])
async def send_film(message: types.Message, state: FSMContext):
    """
    Обработка запроса на поиск фильма или сериала, при первом запросе,
    последующие запросы обрабатываются в состоянии
    """
    await add_user_in_db(user_id=message.from_user.id)
    await send_films(message=message, state=state)
    await ChoiceFilmState.first()
