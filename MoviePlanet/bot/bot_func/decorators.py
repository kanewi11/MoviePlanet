from typing import Union
from functools import wraps

from aiogram import types
from aiogram.dispatcher import FSMContext

from ..models import Admin
from ..config import CHANNELS_TO_SUBSCRIBE
from ..messages import msg_if_not_subscribed
from ..keyboards import kb_admin
from .. import bot, session


async def get_need_object_from_args(args: tuple, kwargs: dict, cls: type) -> Union[None, object, type(None)]:
    """
    Возвращаем объект принадлежащий нужному классу из аргументов.

    :param args: Аргументы
    :param kwargs: Именованные аргументы
    :param cls: Класс
    :return: Объект принадлежащий классу
    """

    for arg in args:
        if isinstance(arg, cls):
            return arg

    for _, value in kwargs.items():
        if isinstance(value, cls):
            return value

    return None


def only_admin(func):
    """Функция вызовется, если user является админом"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        message = await get_need_object_from_args(args, kwargs, types.Message)

        is_admin = session.query(Admin).filter(Admin.user_id == message.from_user.id).first()
        if not is_admin:
            return

        await func(*args, **kwargs)
    return wrapper


def subscribers_only(func):
    """
    Функция 'func' вызовется, если user подписан на все группы, иначе,
    высылается сообщение о том что нужно подписаться
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        message = await get_need_object_from_args(args, kwargs, types.Message)

        for group in CHANNELS_TO_SUBSCRIBE:
            from .utils import set_last_message_id_in_db, delete_last_user_message
            user_channel_status = await bot.get_chat_member(chat_id=group, user_id=message.from_user.id)
            if user_channel_status['status'] == 'left':
                await delete_last_user_message(message=message)
                subscribe_msg = await bot.send_message(message.from_user.id, msg_if_not_subscribed)
                await set_last_message_id_in_db(user_id=message.from_user.id, message_id=subscribe_msg.message_id)
                return

        await func(*args, **kwargs)

    return wrapper


def cancel_handler(func):
    """Отмена выполнения функции и завершение состояния"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        message = await get_need_object_from_args(args, kwargs, types.Message)
        state = await get_need_object_from_args(args, kwargs, FSMContext)
        if message.text.startswith('/') or message.text == 'Отмена':
            await message.answer(text='Операция отменена!', reply_markup=kb_admin)
            return await state.finish()

        await func(*args, **kwargs)
    return wrapper
