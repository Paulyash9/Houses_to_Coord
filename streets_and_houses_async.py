import aiohttp
import asyncio
import json
import requests as req
import unicodedata as ud
from bs4 import BeautifulSoup
from settings import *
from datetime import datetime


def timeit(func):
    def wrapper(*args, **kwargs):
        start = datetime.now()
        result = func(*args, **kwargs)
        print(f"Выполнено за {datetime.now() - start}")
        return result

    return wrapper


def region_and_links() -> tuple:
    session = req.Session()
    soup = BeautifulSoup(session.get(base_url, headers=headers).content, 'html5lib')
    region = soup.find('h1').text.split(', ')[0]

    file = f'parsed {region}.json'
    urls = get_links(soup)
    url_list = urls.copy()
    for settlement, settlement_url in urls.items():
        if check_file(settlement, file):
            url_list.pop(settlement)
    print(f'Регион: {region}'
          f'Общее количество районов и городов: {len(url_list)}')

    return region, url_list


def get_links(soup: BeautifulSoup) -> dict or bool:
    urls = {}
    for i in soup.find_all('div', class_="col-md-3 col-sm-6"):
        urls.update({
            ud.normalize("NFKD", i.find('a').text.replace(u'\xa0', u' ')):
                'https://фиас.онлайн' + i.find('a').get('href')
        })

    return urls if len(urls) > 0 else False


def get_houses(soup: BeautifulSoup) -> list or bool:
    house = [i.text for i in soup.select("table.table:not(.table-striped.table-hover) "
                                         "> tbody "
                                         "> tr "
                                         "> td:nth-child(2) "
                                         "> a")]
    house = list(set(house))  # удаляем дубликаты
    return house if len(house) > 0 else False


async def gather_and_parse(url_list: dict):
    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.Task(fetch(session, key, url)) for key, url in url_list.items()]
        await asyncio.gather(*tasks)
    return tasks


async def fetch(session, head, url: str = base_url):
    scrapped_data = []
    async with session.get(url, headers=headers) as response:
        html = await response.text()
    soup = BeautifulSoup(html, 'html5lib')

    houses = get_houses(soup)
    if houses:
        scrapped_data.extend(houses)

    # get list of links
    links = get_links(soup)
    if links:
        scrapped_data.append(links)
        for link in scrapped_data:
            if isinstance(link, dict):
                [link.update({key: await parsing(url)}) for key, url in link.items()]
    print(f'{head} parsed')
    return {head: scrapped_data}


async def parsing(url: str) -> list:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            html = await response.text()

    soup = BeautifulSoup(html, 'html5lib')

    scrapped_data = []
    houses = get_houses(soup)
    if houses:
        scrapped_data.extend(houses)

    # get list of links
    links = get_links(soup)
    if links:
        scrapped_data.append(links)
        for link in scrapped_data:
            if isinstance(link, dict):
                [link.update({key: await parsing(url)}) for key, url in link.items()]
    return scrapped_data


def check_file(settlement, file):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            opened_file = json.load(f)
        for i in opened_file:
            if settlement in i.keys():
                print(f'{settlement} уже есть')
                return True
        return False
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        with open(file, 'w', encoding='utf-8') as f:
            f.close()
        return False


def save_file(data, file):
    exist_data = list()
    try:
        with open(file, 'r', encoding='utf-8') as f:
            exist_data = list(json.load(f))
    except (json.decoder.JSONDecodeError, FileNotFoundError):
        exist_data = list()
    exist_data.extend(data)
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(exist_data, f, indent=4, ensure_ascii=False)


@timeit
def main():
    # 1. preparing and checking exists data
    region, url_list = region_and_links()  # get region name and list of first URLs
    file = f'parsed {region}.json'

    # 2. parsing
    loop = asyncio.get_event_loop()
    data = loop.run_until_complete(gather_and_parse(url_list))

    # 3. cleaning
    clean_data = []
    for d in data:
        clean_data.append(d.result())

    # 4. saving
    save_file(clean_data, file)


if __name__ == '__main__':
    main()
