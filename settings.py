"""Неизменяемые данные"""
'''
здесь должен быть API "JavaScript API и HTTP Геокодер" из https://developer.tech.yandex.ru/services/
бесплатный API позволяет спарсить до 25 000 адресов
'''

API = ''  # вставить API сюда

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/81.0.4044.129 Safari/537.36 '}

"""Изменяемые данные"""

url = 'http://www.ifias.ru/316934/802441.html'  # найти город и взять url с сайта ifias.ru

