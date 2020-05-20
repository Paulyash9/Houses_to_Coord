import pandas as pd
import requests as req
from bs4 import BeautifulSoup
from settings import *


def take_streets():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/81.0.4044.129 Safari/537.36 '}
    response = req.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'lxml').find_all('a', href=True, title=True)

    all_streets = dict()
    for street in soup:
        if street.text not in exclude:
            all_streets[street.text] = street['href']
    return all_streets


def take_houses(street_url):  # парсим дома
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/81.0.4044.129 Safari/537.36 '}
    response = req.get(street_url, headers=headers)
    soup = BeautifulSoup(response.content, 'lxml').find_all('td')

    # чистим данные (ОКВЭД, ОКАТО итд)
    exclude_2 = ' / '
    no_houses = 'Данная улица не содержит домов с номерами.'
    houses = []
    house = ''
    # собираем дома (цикл останавливается на ОКТМО на каждой строчке и собирает 3 тэга перед ним: дом, корпус, литер)
    for i in range(len(soup)):
        if soup[i].text is no_houses:
            break
        if soup[i].text in exclude_oktmo and soup[i].text is not '':
            for n in range(1, 4):
                if exclude_2 in soup[i - n].text:
                    break
                else:
                    house = f'{soup[i - n].text} {house}'
            houses.append(house)
            house = ''

    # убираем лишние пробелы и обозначение домовладений в стоке
    suffix_1 = ' д/вл'
    suffix_2 = ' вл'
    for num, house in enumerate(houses):
        houses[num] = house.rstrip()
        if house.endswith(suffix_1):
            houses[num] = house[:-len(suffix_1)]
        if house.endswith(suffix_2):
            houses[num] = house[:-len(suffix_2)]

    # убираем дубликаты
    houses = list(dict.fromkeys(houses))

    return houses  # возращаем список домов на улице


def to_excel():
    list_of_houses = dict()
    completed = 0

    # парсим улицы
    streets = take_streets()

    # парсим дома
    for street, street_url in streets.items():
        list_of_houses[street] = take_houses(street_url)
        completed += 1
        print(f'{completed} из {len(streets.keys())}')

    # сохраняем
    df = pd.DataFrame([(key, var) for (key, L) in list_of_houses.items() for var in L], columns=['Улица', 'Дом'])
    df['Город'] = [city] * len(df['Улица'])
    columns_titles = ['Город', 'Улица', 'Дом']
    df = df.reindex(columns=columns_titles)  # меняем колонки местами на 'Город', 'Улица', 'Дом'
    df.to_excel(f'houses_{city}.xlsx', sheet_name='Sheet1', index=None)
    print(f'Сохранено в houses_{city}.xlsx')


if __name__ == '__main__':
    to_excel()
