import pandas as pd
import requests as req
from bs4 import BeautifulSoup
from settings import *


def take_city():
    response = req.get(url, headers=headers)
    city = BeautifulSoup(response.content, 'lxml').find('title').text.split(' Город')[0]
    return city


def take_coords(address):  # парсим коодинаты из адресов
    response = req.get(f'https://geocode-maps.yandex.ru/1.x/?apikey={API}&geocode={address}&format=json').json()
    if response['response']['GeoObjectCollection']['metaDataProperty']['GeocoderResponseMetaData']['found'] is '0':
        return 'None None'
    else:
        response = response['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']
        return response


def coords_to_df(city):  # формируем таблицу из адресов и координат
    houses = pd.read_excel(f'houses_{city}.xlsx', sheet_name='Sheet1', index_col=0)
    lon = list()
    lat = list()
    completed = 0
    for row in range(len(houses)):
        address = f"{city}+{houses['Улица'][row]}+{houses['Дом'][row]}"
        try:
            x, y = take_coords(address).split(' ')
        except AttributeError:
            x, y = take_coords(address)[0]
        lon.append(x)
        lat.append(y)
        completed += 1
        if completed % 100 == 0:
            print(f'{completed} из {len(houses)}')
            backup_file(lon, lat)  # делается бэкап на всякий случай
        if completed == len(houses):
            print(f'{completed} из {len(houses)}')
    houses['lon'] = lon
    houses['lat'] = lat
    return houses


def create_file(city):
    with open(f'parsed_{city}.txt', 'w', encoding='utf-8') as file:
        file.write('city_name,geometry_name,building_name,lon,lat\n')


def backup_file(lon, lat):
    df = pd.DataFrame(list(zip(lon, lat)),
                      columns=['lon', 'lat'])
    df.to_csv(f'backup_parsed_{city}.txt', index=False, header=False, sep=',', mode='a')


def save_file(city, df):
    df.to_csv(f'parsed_{city}.txt', header=False, sep=',', mode='a')


if __name__ == '__main__':
    city = take_city()
    create_file(city)
    save_file(city, coords_to_df(city))
    print(f'Сохранено в parsed_{city}.txt')
