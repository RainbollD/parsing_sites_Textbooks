import sys
import requests
from bs4 import BeautifulSoup
import os
import json


def read_json(file_name):
    if not os.path.exists(file_name):
        raise FileNotFoundError(f"Файл {file_name} не найден.")
    with open(file_name, 'r') as f_json:
        f_json = json.load(f_json)
        if not isinstance(f_json, dict):
            raise ValueError(f"Неверный формат данных в файле.")
        if any(key not in f_json for key in ['url', 'output']):
            print(
                f"В файле отсутствует: "
                f"{"url (ссылка на сайт)" if "url" not in f_json else "output (имя файла для вывода)"}")
            sys.exit(1)
        return f_json['url'], f_json['output']


def main():
    try:
        settings_file = 'settings.json'
        url, out_file = read_json(settings_file)
        print(url, out_file)
    except FileNotFoundError as e:
        print(e)
    except ValueError as e:
        print(e)
    else:
        print("Успешно!")


if __name__ == "__main__":
    main()
