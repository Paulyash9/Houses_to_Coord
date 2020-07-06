import json

import pandas as pd
import requests as req

from settings import API
from streets_and_houses import take_region


def take_coords(address):  # парсим коодинаты из адресов
    response = req.get('https://geocode-maps.yandex.ru/1.x/?apikey={0}&geocode={1}&format=json'
                       .format(API, address)).json()
    if response['response']['GeoObjectCollection']['metaDataProperty']['GeocoderResponseMetaData']['found'] == '0':
        return 'None None'
    return response['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']


def json_data():
    with open('parsed {0}.json'.format(Region), 'r', encoding='utf-8') as check_end_file:
        houses = json.load(check_end_file)
    return houses


def coords_to_json(houses):  # формируем таблицу из адресов и координат
    if End - 1 > len(houses):
        raise ValueError('"End" is out of range, max range is {0}. Change value of "End"'.format(len(houses)))
    else:
        geocode = list()
        completed = 0
        count = check_count(houses)
        if count:
            for row in range(Start_from, End - 1):  # по городам/районам
                for key, lvl0 in houses[row].items():  # по улицам/поселкам
                    if isinstance(lvl0, list):
                        for i in lvl0:
                            address = "Россия+{0}+{1}+{2}".format(Region, key, i)
                            try:
                                x, y = take_coords(address).split(' ')
                            except AttributeError:
                                x, y = take_coords(address)[0]
                            geocode.append([Region, key, i.upper(), x, y])
                            completed += 1
                            backup_file(geocode, completed, count) if completed % 100 == 0 else 0
                    else:
                        for key1, lvl1 in lvl0.items():
                            if isinstance(lvl1, list):
                                for i in lvl1:
                                    address = "Россия+{0}+{1}+{2}+{3}".format(Region, key, key1, i)
                                    try:
                                        x, y = take_coords(address).split(' ')
                                    except AttributeError:
                                        x, y = take_coords(address)[0]
                                    geocode.append([key, key1, i.upper(), x, y])
                                    completed += 1
                                    backup_file(geocode, completed, count) if completed % 100 == 0 else 0
                            else:
                                for key2, lvl2 in lvl1.items():
                                    if isinstance(lvl2, list):
                                        for i in lvl2:
                                            address = "Россия+{0}+{1}+{2}+{3}+{4}".format(Region, key, key1, key2, i)
                                            try:
                                                x, y = take_coords(address).split(' ')
                                            except AttributeError:
                                                x, y = take_coords(address)[0]
                                            geocode.append([key1, key2, i.upper(), x, y])
                                            completed += 1
                                            backup_file(geocode, completed, count) if completed % 100 == 0 else 0
                                    else:
                                        for key3, lvl3 in lvl2.items():
                                            if isinstance(lvl3, list):
                                                for i in lvl3:
                                                    address = "Россия+{0}+{1}+{2}+{3}+{4}+{5}".format(
                                                        Region, key, key1, key2, key3, i)
                                                    try:
                                                        x, y = take_coords(address).split(' ')
                                                    except AttributeError:
                                                        x, y = take_coords(address)[0]
                                                    geocode.append([key2, key3, i.upper(), x, y])
                                                    completed += 1
                                                    backup_file(geocode, completed, count) if completed % 100 == 0 \
                                                        else 0
            return geocode


def check_count(houses):
    count = 0
    for a in range(Start_from, End - 1):
        for lv1 in houses[a].values():
            if isinstance(lv1, list):
                count += len(lv1)
            else:
                for lv2 in lv1.values():
                    if isinstance(lv2, list):
                        count += len(lv2)
                    else:
                        for lv3 in lv2.values():
                            if isinstance(lv3, list):
                                count += len(lv3)
    if count < 25000:  # ограничение использования бесплатного API яндекса
        return count
    else:
        answer = input('Запросов больше 25 000 ({0}). '
                       'Вы уверены, что хотите все отпарсить? (y/n) '.format(count))
        if answer.lower() == 'y':
            return count
    return False


def backup_file(geocode, completed, count):
    df = pd.DataFrame(geocode,
                      columns=['city_name', 'geometry_name', 'building_name', 'lon', 'lat'])
    df.to_csv('backup_parsed {0} ({1}-{2}).txt'.format(Region, Start_from, End),
              index=False, sep=',', mode='w')
    print('Бэкап {0} записей из {1}'.format(completed, count))


def save_file(geocode):
    if geocode is not None:
        df = pd.DataFrame(geocode, columns=['city_name', 'geometry_name', 'building_name', 'lon', 'lat'])
        df.to_csv('parsed {0} ({1}-{2}).txt'.format(Region, Start_from, End), index=False, sep=',', mode='w')
        print('Сохранено в parsed_{0}({1}-{2}).txt'.format(Region, Start_from, End))


def start_parse():
    if Start_from < End:
        save_file(coords_to_json(houses))
    if Start_from >= End:
        raise ValueError('Start_from >= End')


if __name__ == '__main__':
    Region = take_region()

    # с какого города/района по порядку начинать парсить(начиная с 0)
    Start_from = 6

    # до какого города ВКЛЮЧИТЕЛЬНО по порядку парсить
    # (если указать None, то будет парсить до самого конца)
    End = None

    houses = json_data()
    if End is None:
        End = len(houses) + 1

    start_parse()
