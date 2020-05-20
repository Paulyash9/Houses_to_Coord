import pandas as pd
import requests as req
from bs4 import BeautifulSoup
from settings import *


def take_region(reg_url):
    response = req.get(f'http://www.ifias.ru{reg_url}', headers=headers)
    region = BeautifulSoup(response.content, 'lxml').find('h2').text
    region = region.split()[0]
    return region


def take_streets_oktmo():
    response = req.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'lxml')
    links = soup.find_all('a', href=True, title=True)
    region = take_region(soup.find('a', title="обл")['href'])
    region_num = soup.find('a', title='обл').text
    city = soup.find('title').text.split(',')[0]
    oktmo = soup.find('p', title=f'Общероссийский классификатор территорий муниципальных образований для {city}').text.split()[1]

    # исключение лишних данных при парсинге (при необходимости добавить)
    exclude = ('На главную', 'Главная', 'ФНС РФ', city, region, region_num)

    all_streets = dict()
    for street in links:
        if street.text not in exclude:
            all_streets[street.text] = street['href']
    return all_streets, oktmo, city


def take_houses(street_url, oktmo):  # парсим дома
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
        if soup[i].text in oktmo and soup[i].text is not '':
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
    streets, oktmo, city = take_streets_oktmo()

    # парсим дома
    for street, street_url in streets.items():
        list_of_houses[street] = take_houses(street_url, oktmo)
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
