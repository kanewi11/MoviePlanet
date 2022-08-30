import traceback

from aiogram.utils.exceptions import BadRequest
from aiogram.dispatcher import FSMContext
from aiogram import types

from .utils import make_film_message

from ..config import URL_DEFAULT_POSTER, SITE_URL
from ..keyboards import kb_cancel, kb_start
from .. import session, cb, dp, logging
from ..states import EditPostState
from ..models import Post


@dp.callback_query_handler(cb.filter(action=['delete']))
async def callback_delete_post(call: types.CallbackQuery, callback_data: dict):
    """
    Функция удаления отложенных постов.

    :param call:
    :param callback_data:
    :return:
    """
    p = session.query(Post).filter(Post.id == int(callback_data['id'])).first()
    session.delete(p)

    try:
        session.flush()
    except Exception:
        logging.warning(traceback.format_exc())
        session.rollback()

    await call.message.answer('Пост удален 🗑', reply_markup=kb_start)


@dp.callback_query_handler(cb.filter(action=['edit']), state='*')
async def callback_edit_post(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    """
    Функция изменения времени отправки отложенного поста.

    :param call:
    :param callback_data:
    :param state:
    :return:
    """
    async with state.proxy() as data:
        data['id'] = callback_data['id']

    await call.message.answer('📅 Вышлите дату и время, например:\n\n<b>01.01.2022 09:00</b>', reply_markup=kb_cancel)
    await EditPostState.DATE_TIME.set()


@dp.callback_query_handler(cb.filter(action=['next', 'previous']), state='*')
async def choice_film(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    """
    Функция листания фильмов, то есть пагинация, не самый изящный и понятный алгоритм, но все же работает)

    :param call:
    :param callback_data:
    :param state:
    :return:
    """
    async with state.proxy() as data:
        films = data['films']

    if callback_data['action'] == 'next':
        callback_data['id'] = int(callback_data['id']) + 1
    else:
        callback_data['id'] = int(callback_data['id']) - 1

    id_film = int(callback_data['id'])

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text=f'📺 Смотреть ({id_film + 1} из {len(films)})',
                                            url=f'{SITE_URL}/?q={films[id_film]["player"]["iframe_url"]}'))

    if id_film != len(films) - 1 and id_film != 0:
        keyboard.add(types.InlineKeyboardButton('◀️ Предыдущий', callback_data=cb.new(id=id_film, action='previous')),
                     types.InlineKeyboardButton('Следующий ▶️', callback_data=cb.new(id=id_film, action='next')))
    elif id_film == 0:
        keyboard.add(types.InlineKeyboardButton('Следующий ▶️', callback_data=cb.new(id=id_film, action='next')))
    else:
        keyboard.add(types.InlineKeyboardButton('◀️ Предыдущий', callback_data=cb.new(id=id_film, action='previous')))

    url_photo, caption = await make_film_message(films[id_film])
    photo = types.InputMediaPhoto(media=url_photo, caption=caption)

    try:
        await call.message.edit_media(media=photo, reply_markup=keyboard)
    except BadRequest:
        photo = types.InputMediaPhoto(media=URL_DEFAULT_POSTER, caption=caption)
        await call.message.edit_media(media=photo, reply_markup=keyboard)
