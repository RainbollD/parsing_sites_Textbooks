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
    text = re.sub(r'\r', '', text)
    text = re.sub(r'\n', '. ', text)
    text = re.sub(r'\t', '', text)
    text = re.sub(r'\.\. ', '. ', text)
    text = re.sub(r'\. \. ', '. ', text)
    nltk_text = nltk.sent_tokenize(text, language='russian')
    return [s for s in nltk_text if len(s) != 1]

def del_beginning(tocs, main_text):
    forbidden_words_beg = [
        "часть",
        "содержание",
        "оглавление",
        "введение",
        "заключение",
        "предисловие",
        "аннотация",
        "резюме",
        "глава",
        "параграф",
        "приложение",
        "источник",
        "список литературы",
        "библиография"
    ]
    len_str_main_text = len(main_text)
    clear_line = lambda s: re.sub(r'[^а-яА-ЯёЁa-zA-Z\s]', '', s).strip()
    for toc in tocs:
        toc = clear_line(toc)
        if len(toc) > 1 and toc.lower() not in forbidden_words_beg:
            for idx, line in enumerate(main_text):
                if idx > len_str_main_text * 0.5:
                    continue
                if toc in clear_line(line):
                    return main_text[idx:]

def del_ending(text):
    forbidden_words_end = [
        "оглавление",
        "содержание"
    ]
    len_str_main_text = len(text)
    clear_line = lambda s: re.sub(r'[^а-яА-ЯёЁa-zA-Z\s]', '', s).strip()
    main_text = text
    for idx, line in enumerate(text[::-1]):
        if idx > len_str_main_text * 0.5:
            return main_text
        for word in forbidden_words_end:
            check_line = clear_line(line).lower().strip()
            if word.upper() in line or (word in check_line and len(word) == len(check_line)):
                main_text =  text[:-idx-1]
    return main_text


def find_exercise(tocs, main_text):
    main_text = del_beginning(tocs, main_text)
    main_text = del_ending(main_text)
    return main_text


def divide_toc_text(dirty_text, soup):
    cleaned_text = preprocess_text(dirty_text)
    for idx, sentense in enumerate(cleaned_text):
        if 'Распознанный текст (распознано автоматически без проверок)' in sentense:
            return cleaned_text[:idx], cleaned_text[idx + 1:]
    return cleaned_text, preprocess_text(soup.find(name='div', class_="rasp_txt").text)


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
                dirty_text = soup.find(name='p', class_="MsoPlainText").text
                toc, main_text = divide_toc_text(dirty_text, soup)
                text = find_exercise(toc, main_text)
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
