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


class PDF:

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
        self.text = re.sub(r'\(cid:\d{1,3}\)\n', '', self.text)
        self.text = re.sub(r'\(cid:\d{1,3}\)', '-', self.text)
        self.text = re.sub(r'\"\n', '', self.text)
        self.text = re.sub(r'\"', '-', self.text)
        self.text = re.sub(r'\n', ' ', self.text)
        self.text = re.sub(r' {2}', ' ', self.text)
        self.text = re.sub(r'- ', '', self.text)
        self.text = nltk.sent_tokenize(self.text, language='russian')

    def main(self, is_del_end, do_find_exersice):
        self.transform_text()
        print(4, is_del_end, do_find_exersice)
        if do_find_exersice: self.find_exercise(is_del_end)


class DownloadPdf(GetSettings, PDF):
    def __init__(self):
        super().__init__()
        self.text = ''
        self.url = ''
        self.title = ''
        self.name_pdf = ''
        self.remove_pages = []


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

    def download_pdf(self):
        print(self.url)
        print('8-')
        response = requests.get(self.url)
        print(8)
        self.is_request(response)
        print(9)
        with open(self.name_pdf, 'wb') as f:
            print(10)
            f.write(response.content)

    def extract_text_with_pdfplumber(self):
        print(1)
        self.text = ''
        idx = 1
        with pdfplumber.open(self.name_pdf) as pdf:
            len_pdf_pages = len(pdf.pages)
            for page in pdf.pages:
                idx += 1
                if idx not in self.remove_pages:
                    if not self.is_special_page(page.extract_text()):
                        self.text += 'begin' + page.extract_text()
                    else:
                        if idx > 0.75 * len_pdf_pages:
                            return False
        return True

    def save_json(self):
        with open(self.title, 'w', encoding='utf-8') as f:
            json.dump(self.text, f, ensure_ascii=False, indent=4)

    def download(self):
        self.read_json()
        for book in self.file_data:
            print(-2)
            self.assign_value_to_variable(book)
            print(-3)
            if self.is_url_or_file():
                print(4)
                self.name_pdf = DEFAULT_NAME_PDF
                print(5)
                self.download_pdf()
                print(6)
            else:
                self.name_pdf = self.url
                print(7)
            is_del_end = self.extract_text_with_pdfplumber()
            print(2)
            do_find_exersice = True if self.remove_pages == [] else False
            print(3)
            self.main(is_del_end, do_find_exersice)
            self.save_json()


if __name__ == "__main__":
    DownloadPdf().download()
