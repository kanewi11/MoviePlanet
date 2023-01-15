import traceback

from aiogram.utils.exceptions import BadRequest
from aiogram.dispatcher import FSMContext
from aiogram import types

from .utils import get_caption_for_bot
from .states_group import EditPostState
from ..config import URL_DEFAULT_POSTER, SITE_URL
from ..keyboards import markup_admin, markup_cancel
from .. import cb, dp, logging, Session
from ..models import Post


@dp.callback_query_handler(cb.filter(action=['delete']))
async def callback_delete_post(call: types.CallbackQuery, callback_data: dict):
    """
    Функция удаления отложенных постов.

    :param call:
    :param callback_data:
    :return:
    """
    session = Session()
    post = session.query(Post).filter(Post.id == int(callback_data['id'])).first()

    try:
        session.delete(post)
        session.commit()
    except Exception:
        logging.warning(traceback.format_exc())
        session.rollback()
    finally:
        session.close()

    await call.message.answer('Пост удален 🗑', reply_markup=markup_admin)


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

    await call.message.answer('📅 Вышлите дату и время, например:\n\n<b>01.01.2022 09:00</b>',
                              reply_markup=markup_cancel)
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

    kb_next = types.InlineKeyboardButton('Следующий ▶️', callback_data=cb.new(id=id_film, action='next'))
    kb_previous = types.InlineKeyboardButton('◀️ Предыдущий', callback_data=cb.new(id=id_film, action='previous'))

    if id_film != len(films) - 1 and id_film != 0:  # Если фильм не первый и не последний
        keyboard.add(kb_previous, kb_next)
    elif id_film == 0:  # Если фильм первый
        keyboard.add(kb_next)
    else:  # Если последний
        keyboard.add(kb_previous)

    url_photo, caption = await get_caption_for_bot(films[id_film])
    photo = types.InputMediaPhoto(media=url_photo, caption=caption)

    try:
        await call.message.edit_media(media=photo, reply_markup=keyboard)
    except BadRequest:  # Из-за того, что постер не может загрузиться или открыться в тг, нужно поменять его на наш
        photo = types.InputMediaPhoto(media=URL_DEFAULT_POSTER, caption=caption)
        await call.message.edit_media(media=photo, reply_markup=keyboard)
