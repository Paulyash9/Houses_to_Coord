import json
import requests as req
from my_settings import *
from bs4 import BeautifulSoup


def take_region(url):
    response = req.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'lxml')
    region = soup.find('h2').text.split()[0]
    return region


def take_attributes(soup):
    try:
        region = soup.find('h2').text.split()[0]
    except AttributeError:
        region = ''
    try:
        region_num = soup.find('span', class_="B_currentCrumb").text
    except AttributeError:
        region_num = ''
    try:
        city = soup.find('title').text.split(',')[0]
    except AttributeError:
        city = ''
    try:
        oktmo = int(soup.find('p', title=f'Общероссийский классификатор '
                                         f'территорий муниципальных образований для {city}').text.split()[1])
    except (AttributeError, ValueError):
        oktmo = ''
    return region, region_num, city, oktmo


def take_links(to_exclude, oktmo, exclude_url, url=url):  # сбор ссылок со страницы
    response = req.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'lxml')
    attributes = take_attributes(soup)
    to_exclude.extend(attributes[:-1])
    city = attributes[-2]
    oktmo.add(str(attributes[-1]))
    # убираем дубликаты
    to_exclude = list(dict.fromkeys(to_exclude))
    if type(to_exclude[-1]) is int:
        oktmo.add(str(to_exclude[-1]))
    links = soup.find_all('a', href=True, title=True)
    all_links = dict()

    for link in links:
        if link.text not in to_exclude:
            if link['title'] == 'видео с камеры':
                break
            else:
                if link['href'].split('=')[1] not in exclude_url:
                    all_links[link.text] = link['href']

    if len(all_links.values()) > 0:
        for key, value in all_links.items():
            exclude_value = value.split('=')[1]
            exclude_url.add(exclude_value)
            all_links.update({key: take_links(to_exclude, oktmo, exclude_url, value)})
        return all_links
    else:
        if '/316934/' not in url:
            houses = take_houses(url, oktmo, city)
            return houses
    return all_links


def take_houses(street_url, oktmo, city):  # сбор домов со страницы
    response = req.get(street_url, headers=headers)
    all_soup = BeautifulSoup(response.content, 'lxml')
    soup = all_soup.find_all('td', colspan=False)
    for_oktmo = all_soup.find('h1').text.split(' - ')[0]
    try:
        oktmo_s = int(all_soup.find('p', title=f'Общероссийский классификатор '
                                               f'территорий муниципальных образований для {for_oktmo}').text.split()[1])
        oktmo.add(str(oktmo_s))
    except (AttributeError, ValueError):
        pass
    # чистим список (ОКВЭД, ОКАТО итд)
    exclude_2 = ' / '
    no_houses = 'Данная улица не содержит домов с номерами.'
    houses = []
    house = ''
    # парсим дома (ОКВЭД является триггером для сбора 3 тэгов перед ним: дом, корпус, литер)
    for i in range(len(soup)):
        if soup[i].text is no_houses:
            break
        for okt in oktmo:
            if (soup[i].text in okt and soup[i].text is not '') or (soup[i].text in okt[:-3] and
                                                                    soup[i].text is not ''):
                for n in range(1, 4):
                    if exclude_2 in soup[i - n].text:
                        break
                    else:
                        house = f'{soup[i - n].text} {house}'
                houses.append(house)
                house = ''

    # убирает пробелы
    for num, house in enumerate(houses):
        if house.endswith(' '):
            houses[num] = house.rstrip()

    # убираем домовладения
    suffix_1 = ' д/вл'
    suffix_2 = ' вл'
    for num, house in enumerate(houses):
        if house.endswith(suffix_1):
            houses[num] = house[:-len(suffix_1)]
        if house.endswith(suffix_2):
            houses[num] = house[:-len(suffix_2)]

    # убираем дубликаты
    houses = list(dict.fromkeys(houses))

    return houses


def first_parse(to_exclude, oktmo, url=url):  # сбор ссылок со страницы
    response = req.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'lxml')
    to_exclude.extend(take_attributes(soup))
    # убираем дубликаты
    to_exclude = list(dict.fromkeys(to_exclude))
    if type(to_exclude[-1]) is int:
        oktmo.append(str(to_exclude[-1]))
    links = soup.find_all('a', href=True, title=True)

    all_links = dict()
    for link in links:
        if link.text not in to_exclude:
            if link['title'] == 'видео с камеры':
                break
            else:
                all_links[link.text] = link['href']
    return all_links, to_exclude, oktmo


def check_file(filename, settlement):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            opened_file = json.load(file)
        for i in opened_file:
            if settlement in i.keys():
                print(f'{settlement} уже есть')
                return False
        return True
    except FileNotFoundError:
        with open(filename, 'w', encoding='utf-8') as file:
            file.close()
        return True


def save_file(filename, data, settlement):
    save_data = {settlement: data}
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            exist_data = list(json.load(file))
    except json.decoder.JSONDecodeError:
        exist_data = list()
    exist_data.append(save_data)
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(exist_data, file, indent=4, ensure_ascii=False)


def count(completed, value):
    completed += 1
    print(f'{completed} из {value}')
    return completed


if __name__ == '__main__':
    """ПАРСЕР РАБОТАЕТ ТОЛЬКО НА ОБЛАСТЬ РФ"""
    to_exclude = ['На главную', 'Главная', 'ФНС РФ']
    oktmo = set()
    exclude_url = set()
    completed = 0
    region = take_region(url)
    filename = f'parsed_{region}_обл.json'

    """сбор данных"""
    # 1. с области собираем ссылки на ГОРОДА и РАЙОНЫ
    data = first_parse(to_exclude, oktmo)[0]
    print(f'{len(data.keys())} районов/городов')

    # 2. собираем все дома рекурсией (если есть ссылка дальше - идем на ссылку дальше и тд)
    for settlement, settlement_url in data.items():
        if check_file(filename, settlement):
            data.update({settlement: take_links(to_exclude, oktmo, exclude_url, settlement_url)})
            save_file(filename, data[settlement], settlement)
            completed = count(completed, len(data.keys()))
        else:
            completed = count(completed, len(data.keys()))
