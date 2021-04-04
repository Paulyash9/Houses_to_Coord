import json
import requests as req

from bs4 import BeautifulSoup
from dadata import Dadata
from datetime import datetime
from settings import *


def get_soup() -> BeautifulSoup:
    return BeautifulSoup(req.Session().get(base_url, headers=headers).content, 'html5lib')


def get_json_and_region() -> tuple:
    region = get_soup().find('h1').text.split(', ')[0]
    with open(f'parsed {region}.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data, region


def iter_in_data(value: list, address: list, region: str) -> list:
    address_list = []
    for obj in value:
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, list) and len(value) > 0:
                    full_address = address.copy()
                    full_address.append(key)
                    address_list.extend(iter_in_data(value, full_address, region))
        else:
            full_address = address.copy()
            full_address.append(obj)
            address_list.append(full_address)
    return address_list


def unpack_json(data: list, region: str) -> tuple:
    address_list = []
    for obj in data:
        address = []
        address_new = []
        for key, value in obj.items():
            if len(value) > 0:
                address.extend([region, key])
                address_new = iter_in_data(value, address, region)
                address_list.extend(address_new)
    return address_list, region


def check_file(region: str) -> int:
    try:
        # вычитаем строку с заголовками колонок
        count = sum(1 for _ in open(f'parsed_{region}.txt', encoding='utf-8')) - 1
        print(f"Файл с координатами найден. Адресов: {count}")
        return count
    except FileNotFoundError:
        with open(f'parsed_{region}.txt', 'w', encoding='utf-8', newline='') as file:
            file.write("city_name,geometry_name,building_name,lon,lat\n")
        print(f'Файл не найден, создан parsed_{region}.txt')
        return 0


def get_coords_dadata(address: str, region_code: int) -> str:
    """
    принимает address
    получает lon, lat из API Dadata
    выдаёт строку с координатами
    """
    try:
        result = Dadata(DA_API, DA_SC).suggest("address", address,
                                               locations=[{"kladr_id": region_code}]
                                               )
        if result[0]['data']['geo_lon'] is None:
            result = Dadata(DA_API, DA_SC).suggest('address', address[:address.rfind(',')],
                                                   locations=[{"kladr_id": region_code}]
                                                   )
        return f",{result[0]['data']['geo_lon']},{result[0]['data']['geo_lat']}"
    except IndexError:
        return ',None,None'


def check_remain() -> int:
    """проверка сколько осталось запросов"""
    return 10_000 - Dadata(DA_API, DA_SC).get_daily_stats()['services']['suggestions']


def parse(data: list, region: str) -> print:
    # проверка количества оставшихся запросов
    count = 0
    remain_dadata: int = check_remain()
    count_file: int = check_file(region)

    # номер региона для ограничения поиска координат
    region_code = int(get_soup().select('div.col-md-12.col-sm-12'
                                        '>table.table.table-hover.table-striped'
                                        '> tbody > tr > td:nth-child(2)')[0].text)

    if count_file == len(data):
        return print('Все координаты по данной области собраны.')

    for line in range(count_file, len(data)):
        count += 1
        if remain_dadata - count > 0:
            string: str = ','.join(data[line])
            coordinates: str = get_coords_dadata(string, region_code)

            with open(f'parsed_{region}.txt', 'a', encoding='utf-8') as tmp_file:
                tmp_file.write(f'{",".join(data[line][-3:])}{coordinates}\n')
            print(f'{count_file + count}/{len(data)}') if (count_file + count) % 100 == 0 else 0
        else:
            print(f'Количество запросов больше допустимого на сегодня.\n'
                  f'Осталось адресов: {len(data) - (count_file + count)}')
    return print(f'Данные сохранены в parsed_{region}.txt')


def main():
    # preparing
    start = datetime.now()
    data, region = unpack_json(*get_json_and_region())
    print(f'Регион: {region} \n'
          f'Общее количество адресов: {len(data)}')
    # parsing
    parse(data, region)

    print(f'Выполнено за {datetime.now() - start}')


if __name__ == '__main__':
    main()
