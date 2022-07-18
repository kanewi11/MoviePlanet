import json
import logging
import datetime
import traceback
from aiogram.types import ReplyKeyboardRemove
from aiogram.dispatcher import FSMContext
from aiogram import types
from ..states import ForwardState, PostState, EditPostState
from ..models import User, Admin, Post
from ..search_film import make_post
from ..keyboards import *
from .. import session, dp, bot, MY_CHANNEL_URL


@dp.message_handler(state=ForwardState.cancel_or_message,
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

    chats = []
    users = session.query(User).all()
    for user in users:
        chats.append(user.user_id)

    for chat in chats:
        if message.content_type == 'text':
            try:
                chat_id = await bot.get_chat(chat)
                await bot.send_message(chat_id.id, message.text)
            except:
                pass

        if message.content_type == 'photo':
            try:
                chat_id = await bot.get_chat(chat)

                if message.caption:
                    await bot.send_photo(chat_id.id, message.photo[-1].file_id, caption=message.caption)
                else:
                    await bot.send_photo(chat_id.id, message.photo[-1].file_id)
            except:
                pass

        if message.content_type == 'document':
            try:
                chat_id = await bot.get_chat(chat)
                if message.caption:
                    await bot.send_document(chat_id.id, message.document.file_id, caption=message.caption)
                else:
                    await bot.send_document(chat_id.id, message.document.file_id)
            except:
                pass

        if message.content_type == 'video':
            try:
                chat_id = await bot.get_chat(chat)
                if message.caption:
                    await bot.send_video(chat_id.id, message.video.file_id, caption=message.caption)
                else:
                    await bot.send_video(chat_id.id, message.video.file_id)
            except:
                pass

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
            session.refresh()
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
        async with state.proxy() as data:
            data['data'] = await make_post(response)
        data = data['data']
        caption = f'🎬 <b>{data["title"]}</b>\n\n' \
                  f'🌎 <b>Год и страна:</b> {data["year_country"]}\n' \
                  f'({data["serial"]})\n\n' \
                  f'⭐️ {data["rating"]}\n\n'\
                  f'<i>{data["description"]}</i>\n\n' \
                  f'<b>Бот в закрепе ☝️ </b>'
        await bot.send_photo(chat_id=message.from_user.id,
                             photo=f'https://{data["poster"]}',
                             caption=caption)
        await message.answer('⏱ Выслать сейчас?\n'
                             'Или вышлите дату и время, например:\n\n<b>01.01.2022 09:00</b>', reply_markup=kb_yes)
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
            data = data['data']
            caption = f'🎬 <b>{data["title"]}</b>\n\n' \
                      f'🌎 <b>Год и страна:</b> {data["year_country"]}\n' \
                      f'({data["serial"]})\n\n' \
                      f'⭐️ {data["rating"]}\n\n' \
                      f'<i>{data["description"]}</i>\n\n' \
                      f'<b>Бот в закрепе ☝️ </b>'
            chat_id = await bot.get_chat(MY_CHANNEL_URL)
            await bot.send_photo(chat_id=chat_id.id,
                                 photo=f'https://{data["poster"]}',
                                 caption=caption)

        await message.answer(text='✅ Выслал.', reply_markup=kb_start)
        await state.finish()
        return
    if response == 'Отмена':
        await message.answer('Операция отменена ❌', reply_markup=kb_start)
        await state.finish()
        return
    try:
        async with state.proxy() as data:
            p = Post(post=json.dumps(data['data']),
                     date_time=datetime.datetime.strptime(response.strip(), '%d.%m.%Y %H:%M'),
                     published=False)
            session.add(p)

            try:
                session.commit()
                session.refresh()
            except:
                logging.warning(traceback.format_exc())
                session.rollback()

        await message.answer(f'🕧 Пост будет опубликован {response}', reply_markup=kb_start)
        await state.finish()
    except Exception as error:
        await message.answer(f'Произошла ошибка "{error}" введите дату и время в формате дд.мм.гггг чч:мм',
                             reply_markup=ReplyKeyboardRemove())
