import logging
import traceback
from aiogram.dispatcher import FSMContext
from aiogram import types
from MoviePlanet.bot.states import EditPostState
from MoviePlanet.bot.model import Post
from MoviePlanet.bot.keyboards import *
from MoviePlanet.bot import session, cb, dp


@dp.callback_query_handler(cb.filter(action=["delete"]))
async def callback_delete_post(call: types.CallbackQuery, callback_data: dict):
    p = session.query(Post).filter(Post.id == int(callback_data["id"])).first()
    session.delete(p)

    try:
        session.commit()
        session.refresh()
    except:
        logging.warning(traceback.format_exc())
        session.rollback()

    await call.message.answer('Пост удален 🗑', reply_markup=kb_start)


@dp.callback_query_handler(cb.filter(action=["edit"]), state='*')
async def callback_edit_post(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    async with state.proxy() as data:
        data['id'] = callback_data["id"]

    await call.message.answer(
        '📅 Вышлите дату и время, например:\n\n<b>01.01.2022 09:00</b>',
        reply_markup=kb_cancel)
    await EditPostState.DATE_TIME.set()