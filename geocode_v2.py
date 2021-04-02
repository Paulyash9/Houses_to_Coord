import json
import requests as req

from bs4 import BeautifulSoup
from dadata import Dadata
from settings import *


def get_json_and_region() -> tuple:
    session = req.Session()
    soup = BeautifulSoup(session.get(base_url, headers=headers).content, 'html5lib')
    region = soup.find('h1').text.split(', ')[0]
    with open(f'parsed {region}.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data, region


def loop_in(value: list, address: list, region: str, address_list=None, exists=None) -> list:
    if address_list is None:
        address_list = []
    if exists is None:
        exists = []

    for obj in value:
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, list) and len(value) > 0:
                    full_address = address.copy()
                    full_address.append(key)
                    exists = loop_in(value, full_address, region).copy()
        else:
            full_address = address.copy()
            full_address.append(obj)
            address_list.append(full_address)
        if len(exists) > 0:
            address_list.extend(exists)

    return address_list


def unpack_json(data: list, region: str) -> tuple:
    address_list = []
    for obj in data:
        address = []
        address_new = []
        for key, value in obj.items():
            if len(value) > 0:
                address.extend([region, key])
                address_new = loop_in(value, address, region).copy()
        address_list.extend(address_new) if len(address_new) > 0 else 0
    return address_list, region


def check_file(region: str) -> int:
    try:
        count = sum(1 for _ in open(f'parsed_{region}.txt')) - 1  # вычитаем строку с заголовками колонок
        print(f"Файл с координатами найден. Адресов: {count - 1}")
        return count
    except FileNotFoundError:
        with open(f'parsed_{region}.txt', 'w', encoding='utf-8', newline='') as file:
            file.write("city_name,geometry_name,building_name,lon,lat\n")
        print(f'Файл не найден, создан parsed_{region}.txt')
        return 0


def get_coords_dadata(address: str) -> str:
    """
    принимает address
    получает lon, lat из API Dadata
    выдаёт строку с координатами
    """
    result = Dadata(DA_API, DA_SC).suggest("address", address)
    if result[0]['data']['geo_lon'] is None:
        result = Dadata(DA_API, DA_SC).suggest("address", address[:address.rfind(',')])
    return f",{result[0]['data']['geo_lon']},{result[0]['data']['geo_lat']}"


def check_remain() -> int:
    """проверка сколько осталось запросов"""
    return 10_000 - Dadata(DA_API, DA_SC).get_daily_stats()['services']['suggestions']


def parse(data: list, region: str) -> print:
    count = 0
    remain_dadata: int = check_remain()
    count_file: int = check_file(region)

    if count_file == len(data):
        return print('Все координаты по данной области собраны.')

    for line in range(count_file, len(data)):
        count += 1
        if remain_dadata - count > 0:
            string: str = ','.join(data[line])
            coordinates: str = get_coords_dadata(string)

            with open(f'parsed_{region}.txt', 'a', encoding='utf-8') as tmp_file:
                tmp_file.write(f'{",".join(data[line][-3:])}{coordinates}\n')
            print(f'{count_file + count}/{len(data)}') if (count_file + count) % 100 == 0 else 0
        else:
            print(f'Количество запросов больше допустимого на сегодня.\n'
                  f'Осталось адресов: {len(data) - (count_file + count)}')
    return print(f'Данные сохранены в parsed_{region}.txt')


def main():
    # preparing
    data, region = unpack_json(*get_json_and_region())

    # parsing
    parse(data, region)


if __name__ == '__main__':
    main()
