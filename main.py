import requests
import os
import json
import re
import nltk
import pdfplumber
import progressbar

from constants import (FILE_SETTINGS, KEY_SYMBOLS_BEG, KEY_SYMBOLS_END,
                       DEFAULT_NAME_PDF, FOLDER_TESTS, FOLDER_PDF, NTLK_DATA_DIRECTORY)


class GetSettings:
    def __init__(self):
        self.file_data = {}

    @staticmethod
    def is_file():
        """Проверка на наличие файла"""
        if not os.path.exists(FILE_SETTINGS):
            raise FileNotFoundError(f"Файл {FILE_SETTINGS} не найден.")

    def is_dict(self):
        """Проверка, что передаваемы данные - это словарь"""
        if not isinstance(self.file_data, dict):
            raise ValueError("Неверный формат данных в файле.")

    def read_json(self):
        """
        Чтение из файла settings.json
        Загрузка данных книг в self.file_data
        """
        self.is_file()
        with open(FILE_SETTINGS, 'r', encoding="utf8") as data:
            self.file_data = json.load(data)
            self.is_dict()
            self.file_data = self.file_data['books']


class TransformData:

    def del_begin(self):
        """
        Поиск момента с которого начинаются упражнения,
        путем поиска наличия особого символа в строке "KEY_SYMBOLS_BEG"
        :return:
        """
        len_data = len(self.text)
        for idx, line in enumerate(self.text):
            if any(key in line for key in KEY_SYMBOLS_BEG):
                self.text = self.text[idx + 1:]
                return
            if idx > 0.5 * len_data: return

    def transform_text(self):
        """
        Преобразование сырых данных из pdf
        :return:
        """
        self.text = re.sub(r'begin.*?\n', ' ', self.text)
        self.text = re.sub(r'.*?end', '', self.text)
        self.text = re.sub(r'\(cid:\d{1,3}\)\n', '', self.text)
        self.text = re.sub(r'\(cid:\d{1,3}\)', '-', self.text)
        self.text = re.sub(r'\"\n', '', self.text)
        self.text = re.sub(r'\"', '-', self.text)
        self.text = re.sub(r'\n', ' ', self.text)
        self.text = re.sub(r' {2}', ' ', self.text)
        self.text = re.sub(r'- ', '', self.text)
        self.text = re.sub(r'­ ', '', self.text)
        self.text = re.sub(r'­', '-', self.text)
        self.text = nltk.sent_tokenize(self.text, language='russian')

    def control_transform(self):
        """
        Вызов трансформации текста и поиска упражнений
        :return:
        """
        self.transform_text()
        self.del_begin()


class BasicControl(GetSettings, TransformData):
    def __init__(self):
        super().__init__()
        self.text = ''
        self.url = ''
        self.title = ''
        self.name_file = ''
        self.remove_pages = []
        self.up_down = 'up'
        self.widgets = [progressbar.Percentage(),
                        progressbar.Bar('█', ' [', ']')]

    def is_request(self, request):
        """
        Проверка запроса
        :param request:
        :return:
        """
        if not request.status_code == 200:
            raise requests.ConnectionError("Status code {}, url: {}".format(request.status_code, self.url))

    @staticmethod
    def is_special_page(page):
        """
        Проверка на особую страницу (страницы не содержащей упражнения),
        путем поиска в начале страницы особых символов "KEY_SYMBOLS_END"
        :param page: Страница, полученная из pdf
        :return:
        """
        return any(key == line or key.upper() == line for key in KEY_SYMBOLS_END for line in page.split('\n')[:2])

    def is_url_or_file(self):
        """
        Проверка, self.url - ссылка на сайт или файл pdf
        :return:
        """
        regex = re.compile(r'^(?:http|ftp)s?://', re.IGNORECASE)
        return re.match(regex, self.url) is not None

    def add_begin_end(self, page):
        """
        Добавление специальных обозначений в начало или конец страницы,
        для определения в дальнейшем места оглавления
        :param page: Страница книги
        :return:
        """
        if self.up_down == 'up':
            self.text += 'begin' + page
        else:
            self.text += page + 'end'

    def remove_pages_from_settings(self, pdf):
        """
        Удаление страниц из массива self.remove_pages
        :param pdf: Pdf книга
        :return:
        """
        self.text = ''
        for num, page in enumerate(pdf):
            if num not in self.remove_pages:
                self.add_begin_end(page.extract_text())
            self.remove_pages.pop(0)
            if len(self.remove_pages) == 0:
                return

    def remove_special(self, pdf):
        """
        Перебирает страницы книги для выявления особых страниц (не содержащих страниц).
        Не сохраняет данные особой страницы.
        :param pdf: Pdf книга
        :return: True: Не найдено особых страниц после 75%
                 False: После 75% текста, если находит особую странцу
        """
        self.text = ''
        len_pdf_pages = len(pdf)
        for num, page in enumerate(pdf):
            if len_pdf_pages * 0.3 <= num <= len_pdf_pages * 0.7:
                self.add_begin_end(page.extract_text())
            else:
                if not self.is_special_page(page.extract_text()):
                    self.add_begin_end(page.extract_text())
                elif num > len_pdf_pages * 0.7:
                    return

    def up_down_contents(self, pdf):
        """
        Определение расположения нумерации
        :param pdf: Pdf книга
        :return:
        """
        self.up_down = 'up'
        for page in pdf[10:15]:
            string = page.extract_text().split('\n')[0]
            if not re.search(r'\d', string):
                self.up_down = 'down'
                return

    def extract_text_with_pdfplumber(self):
        """
        Открытие файла
        Получение расположение нумерации
        Удаление особых страниц (не содержащих упражений)
        :return: Нужно ли удалять конец True: Да
                                        False: Нет
        """
        with pdfplumber.open(os.path.join(FOLDER_PDF, self.name_file)) as pdf:
            pdf = pdf.pages[2:]
            self.up_down_contents(pdf)
            if len(self.remove_pages) != 0:
                self.remove_pages_from_settings(pdf)
            self.remove_special(pdf)

    @staticmethod
    def create_folder_test():
        if not os.path.exists(FOLDER_TESTS):
            os.makedirs(FOLDER_TESTS)

    def assign_value_to_variable(self, book):
        """
        Присваивание: self.title - название книги,
                      self.url - ссылка на сайт или файл
                      self.remove_pages - странцы, которые нужно удалить
        :param book: Данные книги
        :return:
        """
        self.title = book['title']
        self.url = book['url']
        self.remove_pages = book['remove_pages']

    def download_file_from_url(self):
        """
        Скачивание файла и сохранение под именем self.name_file
        :return:
        """
        response = requests.get(self.url)
        self.is_request(response)
        with open(os.path.join(FOLDER_PDF, self.name_file), 'wb') as f:
            f.write(response.content)

    def download(self, book):
        """
        Присваивает данные
        и скачивает файл, если дана ссылка
        :param book:
        :return:
        """
        self.assign_value_to_variable(book)
        if self.is_url_or_file():
            self.name_file = DEFAULT_NAME_PDF
            self.download_file_from_url()
        else:
            self.name_file = self.url

    def setting_bar(self):
        return progressbar.ProgressBar(widgets=self.widgets, max_value=len(self.file_data),
                                       prefix='Прогресс: ',
                                       fill_char='█')

    def save_json(self):
        """
        Сохранение книги в test_files
        :return:
        """
        self.create_folder_test()
        with open(os.path.join(FOLDER_TESTS, self.title), 'w', encoding='utf-8') as f:
            json.dump(self.text, f, ensure_ascii=False, indent=4)

    def main(self):
        """
        Метод, контролирующий классы.
        :return:
        """
        self.read_json()
        bar = self.setting_bar()
        bar.update(0)
        for i, book in enumerate(self.file_data):
            self.download(book)
            self.extract_text_with_pdfplumber()
            self.control_transform()
            self.save_json()
            bar.update(i + 1)


def auto_nltk_tab():
    """
        Проверка на наличие и установка пакета nltk
        :return:
    """
    nltk.data.path.append(NTLK_DATA_DIRECTORY)
    if not os.path.exists(NTLK_DATA_DIRECTORY):
        os.makedirs(NTLK_DATA_DIRECTORY)

    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', download_dir=NTLK_DATA_DIRECTORY)


if __name__ == "__main__":
    auto_nltk_tab()
    BasicControl().main()
