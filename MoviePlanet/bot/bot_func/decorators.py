import asyncio

from aiogram import types

from ..models import Admin
from ..config import CHANNELS_TO_SUBSCRIBE
from ..messages import msg_if_not_subscribed
from .. import bot, session


async def get_message(args, kwargs):
    """Получаем types.Message из аргументов"""
    message = kwargs.get('message')

    for arg in args:
        if isinstance(arg, types.Message):
            message = arg
    return message


def only_admin(func):
    """Функция вызовется, если user является админом"""
    async def wrapper(*args, **kwargs):
        message = await get_message(args, kwargs)
        if not message:
            return

        is_admin = session.query(Admin).filter(Admin.user_id == message.from_user.id).first()
        if not is_admin:
            return

        await func(*args, **kwargs)
    return wrapper


def subscribers_only(func):
    """
    Функция вызовется, если user подписан на все группы, иначе,
    высылается сообщение о том что нужно подписаться
    """
    async def wrapper(*args, **kwargs):
        message = await get_message(args, kwargs)
        if not message:
            return

        for group in CHANNELS_TO_SUBSCRIBE:
            user_channel_status = await bot.get_chat_member(chat_id=group, user_id=message.from_user.id)
            if user_channel_status['status'] == 'left':
                await bot.send_message(message.from_user.id, msg_if_not_subscribed)
                return

        await func(*args, **kwargs)

    return wrapper
