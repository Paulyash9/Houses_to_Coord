import pandas as pd
import requests as req
from settings import *
from bs4 import BeautifulSoup


def take_streets():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/81.0.4044.129 Safari/537.36 '}
    response = req.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'lxml').find_all('a', href=True, title=True)

    all_streets = {}
    for street in soup:
        if street.text not in exclude:
            all_streets[street.text] = street['href']
    return all_streets


def take_houses(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/81.0.4044.129 Safari/537.36 '}
    response = req.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'lxml').find_all('td')

    # чистим список (ОКВЭД, ОКАТО итд)
    exclude_2 = ' / '
    no_houses = 'Данная улица не содержит домов с номерами.'
    houses = []
    house = ''
    # парсим дома (ОКВЭД является триггером для сбора 3 тэгов перед ним: дом, корпус, литер)
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


def to_excel():
    list_of_houses = dict()
    completed = 0
    streets = take_streets()
    for street, url in streets.items():
        list_of_houses[street] = take_houses(url)
        completed += 1
        print(f'{completed} из {len(streets.keys())}')
    df = pd.DataFrame([(key, var) for (key, L) in list_of_houses.items() for var in L], columns=['Улица', 'Дом'])
    df['Город'] = [city] * len(df['Улица'])
    # свапаем колонки на 'Город', 'Улица', 'Дом'
    columns_titles = ['Город', 'Улица', 'Дом']
    df = df.reindex(columns=columns_titles)
    df.to_excel(f'houses_{city}.xlsx', sheet_name='Sheet1', index=None)


if __name__ == '__main__':
    # print(take_houses(take_streets()['Куйбышева Улица']))
    to_excel()
