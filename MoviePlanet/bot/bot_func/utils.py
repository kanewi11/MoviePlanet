import os
import traceback

import requests
from bs4 import BeautifulSoup as bs

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import BadRequest
from aiogram.utils.exceptions import MessageToDeleteNotFound

from ..config import CHANNELS_TO_SUBSCRIBE, SITE_URL, URL_DEFAULT_POSTER
from ..messages import msg_if_not_subscribed
from ..keyboards import kb_cancel_search
from ..states import ChoiceFilmState
from ..models import User
from .. import bot, session, logging, cb


headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/102.0.0.0 Safari/537.36 '
}

# Домен хранится в файле, открываем файл и записываем домен в переменную domain
with open(os.path.abspath('bot/domain.txt'), 'r') as file:
    domain = file.readline()


async def get_domain():
    """
    В этой функции мы находим новый домен сайта.
    Сайт меняет свой домен раз в ден, старый домен
    устаревает за несколько дней и редирект не происходит.
    1) Отправляем запрос, смотрим url и убираем последний '/'
    2) Записываем новый домен в domain.txt
    """
    global domain
    domain = requests.get(f'{domain}', headers=headers).url[:-1]
    with open(os.path.abspath('bot/domain.txt'), 'w') as file_domain:
        file_domain.write(domain)


async def check_domain(url: str) -> None:
    """
     Если в ссылке не присутствует домен из переменной domain,
     вызываем функцию get_domain(), для того,
     чтобы обновить переменную и файл с доменом.

    :param url: Принимает конечную ссылку после переадресации

    :return: Ничего не возвращает
    """
    if domain not in url:
        await get_domain()


async def find_film(film_name: str) -> list or None:
    """
    Ищем фильмы, передаем в функцию название фильма или сериала
    Если находим возвращаем результат словарей в списке, в противном случае возвращаем None

    :param film_name: Название фильма или сериала

    :return: Возвращает список словарей с данными о фильме или сериале, или ничего
    """
    data = {
        'type': 'search',
        'query': film_name,
        'filter-sort': 'rating_asc'
    }
    results = []
    try:
        response = requests.post(f'{domain}/api/', headers=headers, data=data)
        await check_domain(response.url)
        json_response = response.json()
        pages = json_response['pagination']['pages']
        if pages == 1:
            return json_response['results']
        for page in range(1, pages + 1):
            data['page'] = page
            json_response = requests.post(f'{domain}/api/', headers=headers, data=data).json()
            results += json_response['results']

        del json_response
        return results
    except Exception:
        logging.warning(traceback.format_exc())
        return None


async def add_user_in_db(user_id: str | int):
    user = session.query(User).filter(User.user_id == str(user_id)).first()
    if not user:
        user = User(user_id)
        session.add(user)

        try:
            session.commit()
            session.refresh()
        except:
            logging.warning(traceback.format_exc())
            session.rollback()


async def make_post(url: str) -> dict or None:
    """
    Парсим сайт по ссылке и делаем пост, если все отлично возвращаем словарь,
    в противном случае None

    :param url: Ссылка на фильм или сериал

    :return: Возвращает словарь с данными или ничего
    """
    try:
        response = requests.get(url, headers=headers).text
        soup = bs(response, 'lxml')
        poster = soup.find('img',
                           class_='movie-page-container-main-info__poster__img').get('data-src').replace('//', '')
        title = soup.find('h1', class_='movie-page-container-main-info__data__title_ru').get_text(' ', strip=True)

        year_country = soup.find('div',
                                 class_='movie-page-container-main-info__data__category__line-border'
                                 ).get_text(' ', strip=True)

        description = soup.find('div',
                                class_='movie-page-container-main-info__data__description').get_text(' ', strip=True)
        rating = soup.find('div',
                           class_='movie-page-container-main-info__data__ratings-star'
                           ).find('span').get_text(' ', strip=True)

        try:
            serial = soup.find('span', class_='movie-container_serial').get_text(strip=True)
        except:
            serial = 'Фильм'

        if not serial:
            serial = 'Фильм'

        return {
            'poster': poster,
            'title': title,
            'year_country': year_country,
            'description': description.replace('&quest;', '?'),
            'rating': rating,
            'serial': serial
        }
    except Exception:
        logging.warning(traceback.format_exc())
        return None


async def delete_msg(user_id: str | int, message_id: str | int):
    try:
        await bot.delete_message(user_id, message_id)
    except MessageToDeleteNotFound:
        pass


async def make_film_message(film_data: dict) -> (str, str):
    serial = '\n<b>(Сериал)</b>' if film_data['type'] == 'serial' else ''
    caption = f'<b>📽 {film_data["title_ru"]}</b>{serial}\n\n' \
              f'<b>Озвучка</b>: {film_data["player"]["translator"]}\n\n ' \
              f'⭐ {film_data["rating"]}'
    url_photo = f'https://{film_data["poster"].replace("//", "").replace("170-233", "680-1000")}'
    return url_photo, caption


async def set_last_message_id_in_db(user_id: str | int, message_id: str | int):
    user = session.query(User).filter(User.user_id == user_id).first()
    user.last_message_id = int(message_id)
    try:
        session.commit()
        session.refresh()
    except TypeError:
        session.rollback()
    except Exception:
        logging.warning(traceback.format_exc())
        session.rollback()


async def check_subscribe(user_id: str | int) -> bool:
    for group in CHANNELS_TO_SUBSCRIBE:
        user_channel_status = await bot.get_chat_member(chat_id=group, user_id=user_id)
        if user_channel_status["status"] == 'left':
            await bot.send_message(user_id=user_id, text=msg_if_not_subscribed)
            return False
    return True


async def send_films(message: types.Message, state: FSMContext):
    """
    Поиск и отправка фильмов и сериалов

    :param message:
    :param state:
    :return:
    """
    await delete_msg(user_id=message.chat.id, message_id=message.message_id)  # Удаляем сообщение пользователя

    user = session.query(User).filter(User.user_id == message.from_user.id).first()
    last_film_message_id = user.last_message_id
    if last_film_message_id:
        await delete_msg(user_id=message.chat.id, message_id=last_film_message_id)  # Удаляем последний фильм
        # Удаляем сообщение после последнего фильма "Чтобы выйти из поиска, нажмите кнопку ⬇️"
        await delete_msg(user_id=message.chat.id, message_id=last_film_message_id + 1)

    if not await check_subscribe(user_id=message.from_user.id):  # Проверяем подписан ли на канал
        return

    if message.text.startswith('/') or message.text == 'Прекратить поиск фильма 🙅‍♂':
        await delete_msg(user_id=message.chat.id, message_id=message.message_id)
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

    url_photo, caption = await make_film_message(film_data=films[0])
    try:
        message_film = await bot.send_photo(chat_id=message.chat.id, photo=url_photo,
                                            caption=caption, reply_markup=keyboard)
    except BadRequest:
        message_film = await bot.send_photo(chat_id=message.chat.id, photo=URL_DEFAULT_POSTER,
                                            caption=caption, reply_markup=keyboard)

    await bot.send_message(message.chat.id, 'Чтобы выйти из поиска, нажмите кнопку ⬇️', reply_markup=kb_cancel_search)
    # Записываем id отправленного сообщения с фильмом/и чтобы при след запросе его удалить
    await set_last_message_id_in_db(user_id=message.from_user.id, message_id=message_film.message_id)
