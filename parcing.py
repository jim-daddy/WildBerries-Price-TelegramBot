import requests
from bs4 import BeautifulSoup


class WildBerries:
    def __init__(self, url):
        self.HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36"
        }
        self.URL = url
        self.response = requests.get(self.URL, headers=self.HEADERS)

    '''Функция парсинга wildberries'''

    def parsing(self):
        try:
            html = BeautifulSoup(self.response.content, "html.parser")
            items = html.select(".app")
            title = html.findAll("div")

            print(title)

            # Если длина items равна одному то присваиваем
            if len(items) == 1:
                title = items[0].find('span', class_='name').get_text(strip=True),
                price = items[0].find('span', class_='final-cost').get_text(strip=True)
                return title, price
            # Ошибка
            else:
                print('Ошибка в присваивании')
                return 'error'

        except Exception as e:
            print('Неправильная ссылка')
            return 'error'

    def link_check(self):
        try:
            response = requests.get(self.URL, headers=self.HEADERS)
            return True
        except Exception as e:
            return False

    def only_price(self):
        soup = BeautifulSoup(self.response.content, "html.parser")
        items = soup.findAll('div', class_='trunkOld')

        # Если длина items равна нулю то присваиваем
        if len(items) == 1:
            price = items[0].find('span', class_='final-cost').get_text(strip=True)
            return price
        # Ошибка
        else:
            print('Ошибка в присваивании')
            return 'error'

    def only_title(self):
        soup = BeautifulSoup(self.response.content, "html.parser")
        items = soup.findAll('div', class_='trunkOld')

        # Если длина items равна нулю то присваиваем
        if len(items) == 1:
            title = items[0].find('span', class_='name').get_text(strip=True)
            return title
        # Ошибка
        else:
            print('Ошибка в присваивании')
            return 'error'

    def image(self):
        soup = BeautifulSoup(self.response.content, "html.parser")
        items = soup.findAll('div', class_='trunkOld')

        # Если длина items равна нулю то присваиваем
        if len(items) == 1:
            image = 'https:' + items[0].find('img', class_='MagicZoomFullSizeImage').get('src')
            return image
        else:
            return 'https://static.tildacdn.com/tild3131-3163-4537-a438-303736303735/empty.png'
