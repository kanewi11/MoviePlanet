from typing import Union
import traceback

import requests
from bs4 import BeautifulSoup as bs

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import MessageToDeleteNotFound, MessageCantBeDeleted

from .decorators import only_admin, subscribers_only
from .states_group import ChoiceFilmState
from ..config import SITE_URL, URL_DEFAULT_POSTER
from ..keyboards import markup_cancel_search, markup_admin
from ..models import User
from .. import bot, session, logging, cb


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/102.0.0.0 Safari/537.36 '
}

API_URL = 'https://api.movielab.pro/api/v2/'
METHOD_SEARCH = 'search'


async def find_film(film_name: str) -> Union[list, None]:
    """
    Ищем фильмы, передаем в функцию название фильма или сериала
    Если находим возвращаем результат словарей в списке, в противном случае возвращаем None

    :param film_name: Название фильма или сериала.
    :return: Возвращает список словарей с данными о фильме или сериале, или ничего
    """
    data = {
        'title': film_name,
        'page': 1,
        'limit': 100
    }

    films = []

    response = requests.post(API_URL + METHOD_SEARCH, headers=HEADERS, json=data)
    if response.status_code != 200:
        return None

    json_response = response.json()

    pages = json_response['pagination']['pages']

    if pages < 2:
        return json_response['results']

    for page in range(1, pages + 1):
        data['page'] = page
        json_response = requests.post(API_URL + METHOD_SEARCH, headers=HEADERS, json=data).json()
        films += json_response['results']

    del json_response
    return films


async def add_user_in_db(user_id: Union[str, int]) -> None:
    """
    Добавление User'а в базу

    :param user_id:
    :return:
    """
    is_new_user = session.query(User).filter(User.user_id == str(user_id)).first()
    if is_new_user:
        return

    user = User(str(user_id))
    try:
        session.add(user)
        session.commit()
    except Exception:
        logging.warning(traceback.format_exc())
        session.rollback()


async def get_data_about_film(url: str) -> Union[dict, None]:
    """
    Парсим сайт по ссылке и делаем пост, если все отлично возвращаем словарь,
    в противном случае None

    :param url: Ссылка на фильм или сериал.
    :return: Возвращает словарь с данными или ничего
    """
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        return None

    soup = bs(response.text, 'lxml')
    poster = soup.find('img', class_='movie-page-container-main-info__poster__img').get('data-src').replace('//', '')
    title = soup.find('h1', class_='movie-page-container-main-info__data__title_ru').get_text(' ')
    year_country = soup.find('div', class_='movie-page-container-main-info__data__category__line-border').get_text(' ')
    description = soup.find('div', class_='movie-page-container-main-info__data__description').get_text(' ')
    rating = soup.find('div', class_='movie-page-container-main-info__data__ratings-star').find('span').get_text(' ')

    serial = soup.find('span', class_='movie-container_serial')
    if serial:
        serial.get_text(strip=True)
    else:
        serial = 'Фильм'

    return {
        'poster': poster,
        'title': title,
        'year_country': year_country,
        'description': description.replace('&quest;', '?'),
        'rating': rating,
        'serial': serial
    }


async def delete_msg(user_id: Union[str, int], message_id: Union[str, int]) -> None:
    """Удаляем сообщение"""
    try:
        await bot.delete_message(user_id, message_id)
    except (MessageToDeleteNotFound, MessageCantBeDeleted):
        pass
    except Exception:
        logging.warning(traceback.format_exc())


async def get_caption_for_bot(film_data: dict) -> (str, str):
    """Создаем описание фильма или сериала, а так же если нет постера, меняем на свой"""
    serial = '\n\n<b>(Сериал)</b>' if film_data['type'] == 'serial' else ''
    caption = f'<b>📽 {film_data["title_ru"]}</b> ({film_data["year"]}){serial}\n\n' \
              f'<b>Озвучка</b>: {film_data["player"]["translator"]}\n' \
              f'<b>Качество</b>: {film_data["player"]["quality"]}\n\n' \
              f'⭐ {film_data["rating"]}'
    poster = film_data["poster"]

    if poster == 'https://api-base.tech/no-poster.jpg' or not poster:
        poster = URL_DEFAULT_POSTER

    return poster, caption


async def set_last_message_id_in_db(user_id: Union[str, int], message_id: Union[str, int]) -> None:
    """Записываем в бд id последнего сообщения пользователя, чтобы его потом удалить"""
    user = session.query(User).filter(User.user_id == user_id).first()
    try:
        user.last_message_id = int(message_id)
        session.commit()
    except Exception:
        logging.warning(traceback.format_exc())
        session.rollback()


async def delete_last_user_message(message: types.Message) -> None:
    """Удаление последнего поиска пользователя"""
    user = session.query(User).filter(User.user_id == message.from_user.id).first()
    last_film_message_id = user.last_message_id
    if last_film_message_id:
        await delete_msg(user_id=message.chat.id, message_id=last_film_message_id)


@subscribers_only
async def send_films(message: types.Message, state: FSMContext) -> None:
    """Поиск и отправка фильмов и сериалов"""
    await delete_msg(user_id=message.chat.id, message_id=message.message_id)  # Удаляем сообщение пользователя
    await delete_last_user_message(message=message)  # Удаляем последнее сообщение (последний поиск)

    if message.text.startswith('/') or message.text == 'Прекратить поиск фильма 🙅‍♂':
        await delete_msg(user_id=message.chat.id, message_id=message.message_id)
        await delete_msg(user_id=message.chat.id, message_id=message.message_id + 1)
        await state.finish()
        return

    message_find = await bot.send_message(message.chat.id, text='🔎 Ищу...\n\n<i>Поиск может занять до 15 секунд.</i>')
    films = await find_film(message.text)
    await delete_msg(user_id=message.chat.id, message_id=message_find.message_id)  # Удаляем сообщение о поиске

    if not films:
        # Если не нашел фильм отсылаем сообщение о том что не нашел и записываем id сообщение в базу
        # для того, чтобы при следующем поиске его удалить
        text_msg = "По вашему запросу ничего не найдено 😕"
        not_found_message = await bot.send_message(chat_id=message.chat.id, text=text_msg)
        await set_last_message_id_in_db(user_id=message.from_user.id, message_id=not_found_message.message_id)
        await state.finish()
        return

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text=f'📺 Смотреть (1 из {len(films)})',
                                            url=f'{SITE_URL}/?q={films[0]["player"]["iframe_url"]}'))
    if len(films) > 1:  # Если фильмов больше чем 1, то добавляем пагинацию и записываем фильмы в машину состояний
        keyboard.add(types.InlineKeyboardButton('Следующий ▶️', callback_data=cb.new(id=0, action='next')))

        async with state.proxy() as data:
            data['films'] = films
        await ChoiceFilmState.FILM_CHOICE.set()
    else:
        await state.finish()

    poster, caption = await get_caption_for_bot(film_data=films[0])
    message_film = await bot.send_photo(chat_id=message.chat.id, photo=poster, caption=caption, reply_markup=keyboard)

    await bot.send_message(message.chat.id, 'Чтобы выйти из поиска, нажмите кнопку ⬇️',
                           reply_markup=markup_cancel_search)
    # Записываем id отправленного сообщения с фильмом/и чтобы при след запросе его удалить
    await set_last_message_id_in_db(user_id=message.from_user.id, message_id=message_film.message_id)


async def forward_message(message: types.Message, user_id: Union[str, int]) -> None:
    """Пересылка сообщения"""
    content_type = message.content_type
    if content_type == 'text':
        await bot.send_message(user_id, message.text)
    elif content_type == 'photo':
        if message.caption:
            await bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption)
        else:
            await bot.send_photo(user_id, message.photo[-1].file_id)
    elif content_type == 'document':
        if message.caption:
            await bot.send_document(user_id, message.document.file_id, caption=message.caption)
        else:
            await bot.send_document(user_id, message.document.file_id)
    elif content_type == 'video':
        if message.caption:
            await bot.send_video(user_id, message.video.file_id, caption=message.caption)
        else:
            await bot.send_video(user_id, message.video.file_id)


async def get_caption_for_channel(data: dict) -> str:
    """Создание описания для поста в группу"""
    caption = f'🎬 <b>{data["title"]}</b>\n\n' \
              f'🌎 <b>Год и страна:</b> {data["year_country"]}\n' \
              f'({data["serial"]})\n\n' \
              f'⭐️ {data["rating"]}\n\n' \
              f'<i>{data["description"]}</i>\n\n' \
              f'<b>Бот в закрепе ☝️ </b>'
    return caption


@only_admin
async def admin_keyboard(message: types.Message):
    """Высылаем кнопки для администратора"""
    await bot.send_message(message.chat.id, text='Вы - администратор 😎', reply_markup=markup_admin)
