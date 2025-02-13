import sys
import requests
from bs4 import BeautifulSoup
import os
import json
import re
import nltk

nltk.download('punkt_tab')


def read_json(file_name):
    # Читает JSON файл и возвращает URL и имя выходного файла.
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


def save_json(file_name, sentences):
    # Сохраняет список предложений в указанный JSON файл.
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(sentences, f, ensure_ascii=False, indent=4)


def preprocess_text(text):
    # Предобрабатывает текст, удаляя лишние символы и форматируя его.
    text = re.sub(r'\r\n', '. ', text)
    text = re.sub(r'\t', '', text)
    text = re.sub(r'\.\.', r'.', text)
    return text


def main():
    # Основная функция, выполняющая процесс извлечения текста с веб-страницы.
    try:
        settings_file = 'settings.json'
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        urls, out_files = read_json(settings_file)
        for url, out_file in zip(urls, out_files):
            request = requests.get(url, headers=headers)
            if request.status_code == 200:
                soup = BeautifulSoup(request.content, 'html.parser')
                text = soup.find(name='div', class_="rasp_txt").text
                text = preprocess_text(text)
                text = nltk.sent_tokenize(text, language='russian')
                save_json(out_file, text)
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
