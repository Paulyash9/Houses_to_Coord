import json
from streets_and_houses import take_region


def file():
    region = take_region()
    with open(f'parsed {region}.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data, region


def all_count():
    data, region = file()
    count = 0
    for a in range(len(data)):
        for lv1 in data[a].values():
            for lv2 in lv1.values():
                if type(lv2) is list:
                    count += len(lv2)
                else:
                    for lv3 in lv2.values():
                        if type(lv3) is list:
                            count += len(lv3)
    return f'Всего адресов: {count}, городов/районов в {region}: {len(data)}'


def check_count(start, end):
    data, region = file()
    count = 0
    if end > len(data):
        raise ValueError(f'в {region} всего {len(data)} городов/районов. Уменьшите значение End')
    for a in range(start, end):
        for lv1 in data[a].values():
            for lv2 in lv1.values():
                if type(lv2) is list:
                    count += len(lv2)
                else:
                    for lv3 in lv2.values():
                        if type(lv3) is list:
                            count += len(lv3)
    return f'В {end - start} городах/районах расположено {count} адресов'


if __name__ == '__main__':
    start = 0
    end = 22
    print(check_count(start, end))
    #print(all_count())
