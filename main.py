import sys
import requests
from bs4 import BeautifulSoup
import os
import json
import re

def read_json(file_name):
    if not os.path.exists(file_name):
        raise FileNotFoundError(f"Файл {file_name} не найден.")
    with open(file_name, 'r', encoding="utf8") as f_json:
        f_json = json.load(f_json)
        if not isinstance(f_json, dict):
            raise ValueError(f"Неверный формат данных в файле.")
        if any(key not in f_json for key in ['url', 'output']):
            print(
                f"В файле отсутствует: "
                f"{"url (ссылка на сайт)" if "url" not in f_json else "output (имя файла для вывода)"}")
            sys.exit(1)
        return f_json['url'], f_json['output']

def save_json(file_name, data):
    pass

def main():
    try:
        settings_file = 'settings.json'
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        url, out_file = read_json(settings_file)

        request = requests.get(url, headers=headers)

        if request.status_code == 200:
            soup = BeautifulSoup(request.content, 'html.parser')
            text = soup.find(name='div', class_="rasp_txt").text
            print(text)
        else:
            print(f"Ошибка при запросе {request.status_code}")
            sys.exit(1)

    except FileNotFoundError as e:
        print(e)
    except ValueError as e:
        print(e)
    else:
        print("Успешно!")


if __name__ == "__main__":
    main()
