import json
import re
import requests as req
import unicodedata as ud
from bs4 import BeautifulSoup
from settings import *


def take_region():
    response = req.get(url, headers=headers)
    region = BeautifulSoup(response.content, 'lxml').find('h1').text.split(', ')[0]
    return region


def take_links(url=url):  # сбор ссылок со страницы
    response = req.get(f'https://фиас.онлайн/{url}', headers=headers)
    soup = BeautifulSoup(response.content, 'lxml').find_all('div', class_="col-md-3 col-sm-6")
    links = dict()
    for i in soup:
        links[ud.normalize("NFKD", i.find('a').text.replace(u'\xa0', u' '))] = i.find('a')['href'][1:]

    if len(links.keys()) > 0:
        for key, value in links.items():
            links.update({key: take_links(value)})
        return links
    else:
        houses = take_houses(url)
        return houses


def take_houses(street):  # сбор домов со страницы
    response = req.get(f'https://фиас.онлайн/{street}', headers=headers)
    soup = BeautifulSoup(response.content, 'lxml')
    soup = soup.find_all('a', href=True, rel=False, class_=False)
    houses = list()
    for i in soup:
        if len(re.findall(r'/', i['href'])) == 2 and re.findall(r'\d', i.text):
            houses.append(i.text)
    return houses


def first_parse():  # сбор ссылок со страницы
    response = req.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'lxml').find_all('div', class_="col-md-3 col-sm-6")
    links = dict()
    for i in soup:
        links[ud.normalize("NFKD", i.find('a').text.replace(u'\xa0', u' '))] = i.find('a')['href'][1:]
    return links


def check_file(settlement):
    try:
        with open(Filename, 'r', encoding='utf-8') as file:
            opened_file = json.load(file)
        for i in opened_file:
            if settlement in i.keys():
                print(f'{settlement} уже есть')
                return False
        return True
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        with open(Filename, 'w', encoding='utf-8') as file:
            file.close()
        return True


def save_file(data, settlement):
    save_data = {settlement: data}
    try:
        with open(Filename, 'r', encoding='utf-8') as file:
            exist_data = list(json.load(file))
    except json.decoder.JSONDecodeError:
        exist_data = list()
    exist_data.append(save_data)
    with open(Filename, 'w', encoding='utf-8') as file:
        json.dump(exist_data, file, indent=4, ensure_ascii=False)


def count(completed, value):
    completed += 1
    print(f'{completed} из {value}')
    return completed


if __name__ == '__main__':
    completed = 0
    Region = take_region(url)
    Filename = f'parsed {Region}.json'

    """сбор данных"""
    # 1. с области собираем ссылки на ГОРОДА и РАЙОНЫ
    data = first_parse()
    print(f'{len(data.keys())} районов/городов')

    # 2. собираем все дома рекурсией (если есть ссылка дальше - идем на ссылку дальше и тд)
    for settlement, settlement_url in data.items():
        if check_file(settlement):
            data.update({settlement: take_links(settlement_url)})
            save_file(data[settlement], settlement)
            completed = count(completed, len(data.keys()))
        else:
            completed = count(completed, len(data.keys()))
