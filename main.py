import time
from os import times

import requests
import os
import json
import re
import nltk
import pdfplumber

from constants import FILE_SETTINGS, KEY_SYMBOLS_BEG, KEY_SYMBOLS_END, DEFAULT_NAME_PDF


class GetSettings:
    def __init__(self):
        self.file_data = {}

    @staticmethod
    def is_file():
        if not os.path.exists(FILE_SETTINGS):
            raise FileNotFoundError(f"Файл {FILE_SETTINGS} не найден.")

    def is_dict(self):
        if not isinstance(self.file_data, dict):
            raise ValueError("Неверный формат данных в файле.")

    def read_json(self):
        self.is_file()
        with open(FILE_SETTINGS, 'r', encoding="utf8") as data:
            self.file_data = json.load(data)
            self.is_dict()
            self.file_data = self.file_data['books']


class TransformData:

    def del_begin(self):
        for idx, line in enumerate(self.text):
            for key in KEY_SYMBOLS_BEG:
                if key in line:
                    self.text = self.text[idx + 1:]
                    return

    def del_end(self):
        idx_del = 0
        for idx, line in enumerate(self.text[::-1]):
            if idx > len(self.text) * 0.2:
                self.text = self.text[:-idx_del - 1]
                return
            for key in KEY_SYMBOLS_END:
                if key in line or key.upper() in line:
                    idx_del = idx

    def find_exercise(self, is_del_end):
        self.del_begin()
        if is_del_end: self.del_end()

    def transform_text(self):
        self.text = re.sub(r'begin.*?\n', ' ', self.text)
        self.text = re.sub(r'.*?end', '', self.text)
        self.text = re.sub(r'\(cid:\d{1,3}\)\n', '', self.text)
        self.text = re.sub(r'\(cid:\d{1,3}\)', '-', self.text)
        self.text = re.sub(r'\"\n', '', self.text)
        self.text = re.sub(r'\"', '-', self.text)
        self.text = re.sub(r'\n', ' ', self.text)
        self.text = re.sub(r' {2}', ' ', self.text)
        self.text = re.sub(r'- ', '', self.text)
        self.text = nltk.sent_tokenize(self.text, language='russian')

    def control_transform(self, is_del_end, find_exersice):
        self.transform_text()
        if find_exersice: self.find_exercise(is_del_end)


class BasicControl(GetSettings, TransformData):
    def __init__(self):
        super().__init__()
        self.text = ''
        self.url = ''
        self.title = ''
        self.name_file = ''
        self.remove_pages = []
        self.up_down = 'up'

    def is_request(self, request):
        if not request.status_code == 200:
            raise requests.ConnectionError("Status code {}, url: {}".format(request.status_code, self.url))

    @staticmethod
    def is_special_page(page):
        for key in KEY_SYMBOLS_END:
            for line in page.split('\n')[:2]:
                if line == key or key.upper() == line:
                    return True
        return False

    def is_url_or_file(self):
        regex = re.compile(r'^(?:http|ftp)s?://', re.IGNORECASE)
        return re.match(regex, self.url) is not None

    def assign_value_to_variable(self, book):
        self.title = book['title']
        self.url = book['url']
        self.remove_pages = book['remove_pages']

    def download_file_from_url(self):
        response = requests.get(self.url)
        self.is_request(response)
        with open(self.name_file, 'wb') as f:
            f.write(response.content)

    def add_begin_end(self, page):
        if self.up_down == 'up':
            self.text += 'begin' + page
        else:
            self.text += page + 'end'

    def remove_pages_from_settings(self, pdf):
        self.text = ''
        idx = 0
        for page in pdf:
            if idx not in self.remove_pages:
                self.add_begin_end(page.extract_text())
            idx += 1
        return True

    def remove_special(self, pdf):
        self.text = ''
        idx = 0
        len_pdf_pages = len(pdf)
        for page in pdf:
            idx += 1
            if not self.is_special_page(page.extract_text()):
                self.add_begin_end(page.extract_text())
            else:
                if idx > 0.75 * len_pdf_pages:
                    return False
        return True

    def up_down_contents(self, pdf):
        for page in pdf[10:20]:
            string = page.extract_text().split('\n')[0]
            if not bool(re.search(r'\d', string)):
                self.up_down = 'down'
                print(self.url, 'down')
                return
        print(self.url, 'up')

    def extract_text_with_pdfplumber(self):
        with pdfplumber.open(self.name_file) as pdf:
            pdf = pdf.pages
            self.up_down_contents(pdf)
            if len(self.remove_pages) != 0:
                return self.remove_pages_from_settings(pdf)
            return self.remove_special(pdf)

    def save_json(self):
        with open(self.title, 'w', encoding='utf-8') as f:
            json.dump(self.text, f, ensure_ascii=False, indent=4)

    def download(self, book):
        self.assign_value_to_variable(book)
        if self.is_url_or_file():
            self.name_file = DEFAULT_NAME_PDF
            self.download_file_from_url()
        else:
            self.name_file = self.url

    def main(self):
        self.read_json()
        for book in self.file_data:
            self.download(book)
            is_del_end = self.extract_text_with_pdfplumber()
            self.control_transform(is_del_end, self.remove_pages == [])
            self.save_json()


if __name__ == "__main__":
    BasicControl().main()
