from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from proxy_auth_data import login, password

import re


def try_except(func):
    def wrapper(*args, **kwargs):
        try:
            data = func(*args, **kwargs)
        except Exception as e:
            print(e)
            data = None
        return data

    return wrapper


class WildBerries:
    def __init__(self, url):
        self.url = url
        self.html = None
        self.soup = None

    def get_html(self):

        # Использование прокси (увеличивает время работы в 2 раза)
        # proxy_options = {
        #     "proxy": {
        #         "https": f"http://{login}:{password}@38.170.124.35:9719"
        #     }
        # }

        useragent = UserAgent()

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument(f"user-agent={useragent.random}")
        options.add_argument("--disable-blink-features=AutomationControlled")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                                  options=options,) #seleniumwire_options=proxy_options)

        try:
            driver.get(self.url)
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "product-page__grid")))

            self.html = driver.page_source
        except Exception as ex:
            print(ex)
        finally:
            driver.close()
            driver.quit()
        return self.html

    @try_except
    def get_h1(self):
        return self.soup.h1.string

    @try_except
    def get_sku(self):
        return self.soup.find('span', attrs={'id': 'productNmId'}).get_text()

    @try_except
    def get_price(self):
        return self.soup.find('ins', attrs={'class': 'price-block__final-price'}).get_text()

    @try_except
    def get_old_price(self):
        return self.soup.find('del', attrs={'class': 'price-block__old-price'}).get_text()

    @try_except
    def get_brand(self):
        return self.soup.find('div', attrs={'class': 'product-page__header'}).find('a').get_text()

    def get_image(self):
        try:
            return (self.soup.find('div', attrs={'class': 'slide__content img-plug'})
                    .find('img').get('src'))
        except Exception as e:
            print(e)
            return 'https://static.tildacdn.com/tild3131-3163-4537-a438-303736303735/empty.png'

    def parse_data(self):
        self.soup = BeautifulSoup(self.html, 'html.parser')

        h1 = self.get_h1()
        sku = self.get_sku()
        price = self.get_price()
        old_price = self.get_old_price()
        brand = self.get_brand()
        image = self.get_image()

        payload = {
            'h1': h1,
            'sku': sku,
            'price': re.findall(r'[0-9]+', re.sub(r'\xa0', '', price))[0] if price else None,
            'old_price': re.findall(r'[0-9]+', re.sub(u'\xa0', '',
                                                      old_price))[0] if old_price else None,
            'brand': brand,
            'image': image
        }

        return payload
