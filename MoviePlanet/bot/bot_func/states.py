import json
import datetime
import traceback

from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardRemove
from aiogram.dispatcher import FSMContext
from aiogram import types

from .utils import send_films, get_data_about_film, forward_message, get_caption_for_channel
from ..models import Admin, Post, User
from ..config import MY_CHANNEL_URL
from ..keyboards import kb_yes, kb_start
from .. import session, dp, bot, logging


class ForwardState(StatesGroup):
    CANCEL_OR_MASSAGE = State()


class PostState(StatesGroup):
    DATA = State()
    DATE_TIME = State()


class EditPostState(StatesGroup):
    ID = State()
    DATE_TIME = State()


class ChoiceFilmState(StatesGroup):
    FILM_CHOICE = State()


@dp.message_handler(state=ForwardState.CANCEL_OR_MASSAGE,
                    content_types=['video', 'photo', 'document', 'text'],
                    chat_type=types.ChatType.PRIVATE)
async def forward_msg(message: types.Message, state: FSMContext):
    """
    Функция пересылки поста всем пользователям бота и в группу.

    :param message:
    :param state:
    :return:
    """
    if message.text == 'Отмена':
        await message.answer('Операция отменена', reply_markup=kb_start)
        await state.finish()
        return

    if not session.query(Admin).filter(Admin.user_id == message.from_user.id).first():
        return

    users = session.query(User).all()

    for user in users:
        try:
            await forward_message(message=message, user_id=user.user_id)
        except Exception:
            logging.warning(traceback.format_exc())

    await message.answer('Рассылка выполнена', reply_markup=kb_start)
    await state.finish()


@dp.message_handler(state=EditPostState.DATE_TIME, content_types=types.ContentTypes.TEXT)
async def edit_post_date_time(message: types.Message, state: FSMContext):
    """
    Функция изменения времени отложенного поста.

    :param message:
    :param state:
    :return:
    """

    response = message.text
    if response == 'Отмена':
        await message.answer('Операция отменена ❌', reply_markup=kb_start)
        await state.finish()
        return

    try:
        async with state.proxy() as data:
            post_id = data['id']
        date = datetime.datetime.strptime(response.strip(), '%d.%m.%Y %H:%M')
        p = session.query(Post).filter(Post.id == int(post_id)).first()
        if not p:
            await message.answer('Ошибка, пост не найден 😞', reply_markup=kb_start)
            await state.finish()
            return

        p.date_time = date

        try:
            session.commit()
        except:
            logging.warning(traceback.format_exc())
            session.rollback()

        await message.answer(f'✅ Пост будет опубликован {response}', reply_markup=kb_start)
        await state.finish()
        return
    except Exception as error:
        await message.answer(f'😫 Ошибка {error}', reply_markup=kb_start)


@dp.message_handler(state=PostState.DATA)
async def get_post(message: types.Message, state: FSMContext):
    """
    Функция парсинга поста и отправки его админу.

    :param message:
    :param state:
    :return:
    """

    response = message.text
    if response == 'Отмена':
        await message.answer('Операция отменена ❌', reply_markup=kb_start)
        await state.finish()
        return

    await message.answer('⏳ Ожидайте...')
    try:
        post_data = await get_data_about_film(response)
        async with state.proxy() as data:
            data['data'] = post_data

        caption = await get_caption_for_channel(data=post_data)

        await bot.send_photo(chat_id=message.from_user.id,
                             photo=f'https://{post_data["poster"]}',
                             caption=caption)
        await message.answer('⏱ Выслать сейчас?\nИли вышлите дату и время, например:\n\n<b>01.01.2022 09:00</b>',
                             reply_markup=kb_yes)
        await PostState.next()
    except Exception as error:
        await message.answer(f'Произошла ошибка "{error}",\n Попробуйте заново!',
                             reply_markup=kb_start)
        await state.finish()
        return


@dp.message_handler(state=PostState.DATE_TIME)
async def now_or_later(message: types.Message, state: FSMContext):
    """
    Функция отправки поста сейчас или отложить.

    :param message:
    :param state:
    :return:
    """

    response = message.text
    if response == 'Выслать сейчас 🚀':
        await message.answer('💬 Высылаю...', reply_markup=kb_start)
        async with state.proxy() as data:
            post_data = data['data']

        caption = await get_caption_for_channel(data=post_data)
        chat_id = await bot.get_chat(MY_CHANNEL_URL)
        await bot.send_photo(chat_id=chat_id.id, photo=f'https://{post_data["poster"]}', caption=caption)
        await message.answer(text='✅ Выслал.', reply_markup=kb_start)
        await state.finish()
        return
    elif response == 'Отмена':
        await message.answer('Операция отменена ❌', reply_markup=kb_start)
        await state.finish()
        return

    async with state.proxy() as data:
        post_data = data['data']

    post = Post(post=json.dumps(post_data),
                date_time=datetime.datetime.strptime(response.strip(), '%d.%m.%Y %H:%M'),
                published=False)

    try:
        session.add(post)
        session.commit()
    except Exception as error:
        logging.warning(traceback.format_exc())
        session.rollback()
        await message.answer(f'Произошла ошибка "{error}" введите дату и время в формате дд.мм.гггг чч:мм',
                             reply_markup=ReplyKeyboardRemove())

    await message.answer(f'🕧 Пост будет опубликован {response}', reply_markup=kb_start)
    await state.finish()


@dp.message_handler(state=ChoiceFilmState.FILM_CHOICE, content_types=['text'])
async def send_film_state(message: types.Message, state: FSMContext):
    """
    Обработка запроса на поиск фильма или сериала, но в состоянии.

    :param state:
    :param message:
    :return:
    """

    await send_films(message=message, state=state)
