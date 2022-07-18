import logging
import traceback
from aiogram.dispatcher import FSMContext
from aiogram import types
from ..states import EditPostState
from ..models import Post
from ..keyboards import *
from .. import session, cb, dp


@dp.callback_query_handler(cb.filter(action=["delete"]))
async def callback_delete_post(call: types.CallbackQuery, callback_data: dict):
    """
    Функция удаления отложенных постов.

    :param call:
    :param callback_data:
    :return:
    """
    p = session.query(Post).filter(Post.id == int(callback_data["id"])).first()
    session.delete(p)

    try:
        session.commit()
        session.refresh()
    except Exception:
        logging.warning(traceback.format_exc())
        session.rollback()

    await call.message.answer('Пост удален 🗑', reply_markup=kb_start)


@dp.callback_query_handler(cb.filter(action=["edit"]), state='*')
async def callback_edit_post(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    """
    Функция изменения времени отправки отложенного поста.

    :param call:
    :param callback_data:
    :param state:
    :return:
    """
    async with state.proxy() as data:
        data['id'] = callback_data["id"]

    await call.message.answer(
        '📅 Вышлите дату и время, например:\n\n<b>01.01.2022 09:00</b>',
        reply_markup=kb_cancel)
    await EditPostState.DATE_TIME.set()