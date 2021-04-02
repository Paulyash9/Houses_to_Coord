# Houses_to_Coord
Парсер домов в определенном городе России и парсер координат из Dadata.ru API


1. Ввести данные в файл settings.py
2. Запустить streets_and_houses_async.py (streets_and_houses.py работает медленней)
3. Данные запишутся в файл .json
4. Запустить geocode_v2.py
5. На выходе получается файл .txt в формате city_name,geometry_name,building_name,lon,lat
