import sys
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

    def is_url(self):
        if 'url' not in self.file_data:
            print("В файле отсутствует url (ссылка на сайт)")
            sys.exit(1)

    def is_output(self):
        if 'output' not in self.file_data:
            print("В файле отсутствует output (имя файла для вывода)")
            sys.exit(1)

    def read_json(self):
        self.is_file()
        with open(FILE_SETTINGS, 'r', encoding="utf8") as data:
            self.file_data = json.load(data)
            self.is_dict()
            self.is_url()
            self.is_output()

    def get_urls_out_files(self):
        self.read_json()
        return self.file_data['url'], self.file_data['output']


class PDF:
    def del_beg(self):
        idx_del = 0
        for idx, sentense in enumerate(self.text):
            if idx > len(self.text) * 0.05:
                self.text = self.text[idx_del + 1:]
                return
            for key in KEY_SYMBOLS_BEG:
                if key in sentense:
                    idx_del = idx

    def del_end(self):
        idx_del = 0
        for idx, sentense in enumerate(self.text[::-1]):
            if idx > len(self.text) * 0.2:
                self.text = self.text[:-idx_del - 1]
                return
            for key in KEY_SYMBOLS_END:
                if key in sentense or key.upper() in sentense:
                    idx_del = idx

    def find_exercise(self):
        self.del_beg()
        self.del_end()

    def transform_text(self):
        self.text = re.sub(r'begin.*?\n', ' ', self.text)
        self.text = re.sub(r'\(cid:\d{1,3}\)\n', '', self.text)
        self.text = re.sub(r'\(cid:\d{1,3}\)', '-', self.text)
        self.text = re.sub(r'\"\n', '', self.text)
        self.text = re.sub(r'\"', '-', self.text)
        self.text = re.sub(r'\n', ' ', self.text)
        self.text = re.sub(r'  ', ' ', self.text)
        self.text = re.sub(r'- ', '', self.text)
        self.text = nltk.sent_tokenize(self.text, language='russian')

    def main(self):
        self.transform_text()
        self.find_exercise()


class DownloadPdf(GetSettings, PDF):
    def __init__(self):
        super().__init__()
        self.text = ''
        self.url = ''
        self.outfile = ''

    @staticmethod
    def is_request(request):
        if not request.status_code == 200:
            raise requests.ConnectionError("Status code {}".format(request.status_code))

    def download_pdf(self):
        response = requests.get(self.url)
        self.is_request(response)
        with open(DEFAULT_NAME_PDF, 'wb') as f:
            f.write(response.content)

    def extract_text_with_pdfplumber(self):
        self.text = ''
        with pdfplumber.open(DEFAULT_NAME_PDF) as pdf:
            for page in pdf.pages:
                self.text += 'begin' + page.extract_text()

    def save_json(self):
        with open(self.outfile, 'w', encoding='utf-8') as f:
            json.dump(self.text, f, ensure_ascii=False, indent=4)

    def download(self):
        urls, outfiles = self.get_urls_out_files()
        for self.url, self.outfile in zip(urls, outfiles):
            self.download_pdf()
            self.extract_text_with_pdfplumber()
            self.main()
            self.save_json()


if __name__ == "__main__":
    DownloadPdf().download()
