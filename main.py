import sys
import requests
from bs4 import BeautifulSoup
import os
import json
import re
import nltk

nltk.download('punkt')

FORBIDDEN_SYMBOLS_BEG = [
    "часть", "содержание", "оглавление", "введение", "заключение",
    "предисловие", "аннотация", "резюме", "глава", "параграф",
    "приложение", "источник", "список литературы", "библиография", "повторение"
]

KEY_SYMBOLS = ["§"]

FORBIDDEN_SYMBOLS_END = [
    "оглавление", "содержание", "aвторы"
]

FILE_SETTINGS = 'settings.json'
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


class WorkData:
    @staticmethod
    def transform_text(text):
        text = re.sub(r'[\r\t]', '', text)
        text = re.sub(r'\n', '. ', text)
        text = re.sub(r'\.{2,}', '.', text)
        text = re.sub(r'\. \. ', '. ', text)
        nltk_text = nltk.sent_tokenize(text, language='russian')
        return [s for s in nltk_text if len(s) > 1]

    @staticmethod
    def clear_line(line):
        return re.sub(r'[^а-яА-ЯёЁa-zA-Z\s]', '', line).strip()

    @staticmethod
    def del_beginning(tocs, main_text):
        len_str_main_text = len(main_text)
        for toc in tocs:
            toc = WorkData.clear_line(toc)
            if len(toc) > 1 and toc.lower() not in FORBIDDEN_SYMBOLS_BEG:
                for idx, line in enumerate(main_text):
                    if any(special in line for special in KEY_SYMBOLS):
                        return main_text[idx:]
                    if idx > len_str_main_text * 0.5:
                        continue
                    if toc in WorkData.clear_line(line):
                        return main_text[idx:]
        return main_text

    @staticmethod
    def del_ending(text):
        len_str_main_text = len(text)
        main_text = ''
        for idx, line in enumerate(text[::-1]):
            if idx > len_str_main_text * 0.5 and main_text == '':
                return text
            for word in FORBIDDEN_SYMBOLS_END:
                check_line = WorkData().clear_line(line).lower()
                if word.upper() in line or (word in check_line and len(word) == len(check_line)):
                    main_text = text[:-idx - 1]
        return main_text

    @staticmethod
    def find_exercise(tocs, main_text):
        main_text = WorkData.del_beginning(tocs, main_text)
        main_text = WorkData.del_ending(main_text)
        return main_text

    @staticmethod
    def divide_toc_text(dirty_text, soup):
        cleaned_text = WorkData.transform_text(dirty_text)
        for idx, sentence in enumerate(cleaned_text):
            if 'Распознанный текст (распознано автоматически без проверок)' in sentence:
                return cleaned_text[:idx], cleaned_text[idx + 1:]
        return cleaned_text, WorkData.transform_text(soup.find(name='div', class_="rasp_txt").text)

    @staticmethod
    def get_urls_out_files():
        file_data = GetData.read_json()
        return file_data[0], file_data[1]

    @staticmethod
    def save_json(file_name, sentences):
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(sentences, f, ensure_ascii=False, indent=4)


class GetData:
    @staticmethod
    def is_file(file_settings):
        if not os.path.exists(file_settings):
            raise FileNotFoundError(f"Файл {file_settings} не найден.")

    @staticmethod
    def is_dict(file_data):
        if not isinstance(file_data, dict):
            raise ValueError("Неверный формат данных в файле.")

    @staticmethod
    def is_url(file_data):
        if 'url' not in file_data:
            print("В файле отсутствует url (ссылка на сайт)")
            sys.exit(1)

    @staticmethod
    def is_output(file_data):
        if 'output' not in file_data:
            print("В файле отсутствует output (имя файла для вывода)")
            sys.exit(1)

    @staticmethod
    def read_json():
        GetData.is_file(FILE_SETTINGS)
        with open(FILE_SETTINGS, 'r', encoding="utf8") as data:
            file_data = json.load(data)
            GetData.is_dict(file_data)
            GetData.is_url(file_data)
            GetData.is_output(file_data)
            return file_data['url'], file_data['output']


class MainLoop:
    @staticmethod
    def main():
        try:
            urls, outfiles = WorkData.get_urls_out_files()
            for url, out_file in zip(urls, outfiles):
                request = requests.get(url, headers=HEADERS)
                if request.status_code == 200:
                    soup = BeautifulSoup(request.content, 'html.parser')
                    dirty_text = soup.find(name='p', class_="MsoPlainText")
                    if dirty_text is not None:
                        dirty_text = dirty_text.text
                        toc, main_text = WorkData.divide_toc_text(dirty_text, soup)
                        text = WorkData.find_exercise(toc, main_text)
                    else:
                        text = WorkData.transform_text(soup.text)
                    WorkData.save_json(out_file, text)
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
    MainLoop.main()