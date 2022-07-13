import os
import logging
import traceback
from bs4 import BeautifulSoup as bs
import requests


headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/102.0.0.0 Safari/537.36 '
}

# Домен хранится в файле, открываем файл и записываем домен в переменную domain
with open(os.path.abspath('bot/domain.txt'), 'r') as file:
    domain = file.readline()


def get_domain():
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


def check_domain(url):
    """
     Если в ссылке не присутствует домен из переменной domain,
     вызываем функцию get_domain(), для того,
     чтобы обновить переменную и файл с доменом.
    """
    if domain not in url:
        get_domain()


async def find_film(film_name: str) -> list or None:
    """
    Ищем фильмы, передаем в функцию название фильма или сериала
    Если находим возвращаем результат словарей в списке, в противном случае возвращаем None

    :param film_name:
    :return:
    """
    data = {
        'type': 'search',
        'query': film_name,
        'filter-sort': 'rating_asc'
    }
    try:
        response = requests.post(f'{domain}/api/', headers=headers, data=data)
        check_domain(response.url)
        results = response.json()['results']
        return results
    except Exception as error:
        print(error)
        return None


async def make_post(url: str) -> dict or None:
    """
    Парсим сайт по ссылке и делаем пост, если все отлично возвращаем словарь,
    в противном случае None

    :param url:
    :return:
    """
    try:
        response = requests.get(url, headers=headers).text
        soup = bs(response, 'lxml')
        poster = soup.find('img',
                           class_='movie-page-container-main-info__poster__img').get('data-src').replace("//", "")
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
    except Exception as error:
        logging.warning(traceback.format_exc())
        return None
