import json
import pandas as pd


def read_csv():
    df = pd.read_csv('parsed_Ульяновская_обл full.txt', sep=',', encoding='utf-8')
    return df


def read_json():
    with open('parsed Ульяновская Область.json', encoding='utf-8') as f:
        data = json.load(f)
    return data


def change_city(csv_file, json_file):
    completed = 0
    non_completed = 0
    for row in range(len(json_file)):  # по городам/районам ПО СПИСКУ 1,2,3,4,5... 1 уровень
        for key, lvl0 in json_file[row].items():  # по улицам/поселкам (Барыш Город) 2 уровень
            for key1, lvl1 in lvl0.items():  # 42 Стрелковой дивизии Улица 3 уровень
                if type(lvl1) is list:
                    for i in range(len(lvl1)):
                        if csv_file['geometry_name'][completed] == key1:
                            if csv_file['building_name'][completed] in lvl1 \
                                    or f'0{csv_file["building_name"][completed]}' in lvl1:
                                csv_file._set_value(completed, 'city_name', key)
                            else:
                                non_completed += 1
                                print(csv_file['geometry_name'][completed], csv_file['building_name'][completed],
                                      completed)
                        completed += 1

                else:
                    for key2, lvl2 in lvl1.items():  # 4 уровень
                        if type(lvl2) is list:
                            if len(lvl2) > 0:
                                for i in range(len(lvl2)):
                                    if csv_file['geometry_name'][completed] == key2:
                                        if csv_file['building_name'][completed] in lvl2 \
                                                or f'0{csv_file["building_name"][completed]}' in lvl2:
                                            csv_file._set_value(completed, 'city_name', key1)
                                        else:
                                            non_completed += 1
                                            print(csv_file['geometry_name'][completed],
                                                  csv_file['building_name'][completed], completed)
                                    completed += 1

                        else:
                            for key3, lvl3 in lvl2.items():  # 5 уровень
                                if type(lvl3) is list and len(lvl3) > 0:
                                    for i in range(len(lvl3)):
                                        if csv_file['geometry_name'][completed] == key3:
                                            if csv_file['building_name'][completed] in lvl3 \
                                                    or f'0{csv_file["building_name"][completed]}' in lvl3:
                                                csv_file._set_value(completed, 'city_name', key2)
                                            else:
                                                non_completed += 1
                                                print(csv_file['geometry_name'][completed],
                                                      csv_file['building_name'][completed], completed)
                                        completed += 1
    print(f'{non_completed} mistakes')
    print(f'{completed} strings done')
    return csv_file


def upper_houses(df):
    df['building_name'] = df['building_name'].str.upper()
    return df


def save():
    df = change_city(read_csv(), read_json())
    df = upper_houses(df)
    df.to_csv('Ульяновск_changecity.txt', encoding='utf-8-sig', index=False)


if __name__ == '__main__':
    save()
