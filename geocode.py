import json
import pandas as pd
import requests as req
from streets_and_houses import take_region
from settings import *


def take_coords(address):  # парсим коодинаты из адресов
    response = req.get(f'https://geocode-maps.yandex.ru/1.x/?apikey={API}&geocode={address}&format=json').json()
    if response['response']['GeoObjectCollection']['metaDataProperty']['GeocoderResponseMetaData']['found'] is '0':
        return 'None None'
    else:
        response = response['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']
        return response


def coords_to_json():  # формируем таблицу из адресов и координат
    with open(f'parsed {Region}.json', 'r', encoding='utf-8') as file:
        houses = json.load(file)
    if End-1 > len(houses):
        raise ValueError(f'"End" is out of range, max range is {len(houses)}. Change value of "End"')
    else:
        geocode = list()
        completed = 0
        count = check_count(houses)
        if count:
            for row in range(Start_from, End-1):  # по городам/районам
                for key, lvl0 in houses[row].items():  # по улицам/поселкам
                    for key1, lvl1 in lvl0.items():
                        if type(lvl1) is list:
                            for i in lvl1:
                                address = f"{Region}+{key}+{key1}+{i}"
                                try:
                                    x, y = take_coords(address).split(' ')
                                except AttributeError:
                                    x, y = take_coords(address)[0]
                                geocode.append([key, key1, i, x, y])
                                completed += 1
                                backup_file(geocode, completed, count) if completed % 100 == 0 else 0
                        else:
                            for key2, lvl2 in lvl1.items():
                                if type(lvl2) is list:
                                    for i in lvl2:
                                        address = f"{Region}+{key}+{key1}+{key2}+{i}"
                                        try:
                                            x, y = take_coords(address).split(' ')
                                        except AttributeError:
                                            x, y = take_coords(address)[0]
                                        geocode.append([key1, key2, i, x, y])
                                        completed += 1
                                        backup_file(geocode, completed, count) if completed % 100 == 0 else 0
                                else:
                                    for key3, lvl3 in lvl2.items():
                                        if type(lvl3) is list:
                                            for i in lvl3:
                                                address = f"{Region}+{key}+{key1}+{key2}+{key3}+{i}"
                                                try:
                                                    x, y = take_coords(address).split(' ')
                                                except AttributeError:
                                                    x, y = take_coords(address)[0]
                                                geocode.append([key2, key3, i, x, y])
                                                completed += 1
                                                backup_file(geocode, completed, count) if completed % 100 == 0 else 0
            return geocode


def check_count(houses):
    count = 0
    for a in range(Start_from, End-1):
        for lv1 in houses[a].values():
            if type(lv1) is list:
                count += len(lv1)
            else:
                for lv2 in lv1.values():
                    if type(lv2) is list:
                        count += len(lv2)
                    else:
                        for lv3 in lv2.values():
                            if type(lv3) is list:
                                count += len(lv3)
    if count < 25000:
        return count
    else:
        answer = input(f'Запросов больше 25 000 ({count}). Вы уверены, что хотите все отпарсить? (y/n) ')
        return count if answer is 'y' else False


def backup_file(geocode, completed, count):
    df = pd.DataFrame(geocode, columns=['city_name', 'geometry_name', 'building_name', 'lon', 'lat'])
    df.to_csv(f'backup_parsed {Region} ({Start_from}-{End - 1}).txt', index=False, sep=',', mode='w')
    print(f'Бэкап {completed} записей из {count}')


def save_file(geocode):
    if geocode is not None:
        df = pd.DataFrame(geocode, columns=['city_name', 'geometry_name', 'building_name', 'lon', 'lat'])
        df.to_csv(f'parsed {Region} ({Start_from}-{End - 1}).txt', index=False, sep=',', mode='w')
        print(f'Сохранено в parsed_{Region}({Start_from}-{End - 1}).txt')


if __name__ == '__main__':
    Region = take_region()

    # с какого города/района по порядку начинать парсить(начиная с 0)
    Start_from = 0

    # до какого города ВКЛЮЧИТЕЛЬНО по порядку парсить (если указать None, то будет парсить до самого конца)
    End = None

    if End is None:
        with open(f'parsed {Region}.json', 'r', encoding='utf-8') as file:
            houses = json.load(file)
        End = len(houses)+1

    if Start_from < End:
        save_file(coords_to_json())
    if Start_from >= End:
        raise ValueError('Start_from >= End')
