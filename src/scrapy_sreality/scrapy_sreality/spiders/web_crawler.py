import logging
from typing import List, Dict

import scrapy
import sqlalchemy
from bs4 import BeautifulSoup
from scrapy.crawler import CrawlerProcess
from selenium import webdriver
from sqlalchemy.orm import sessionmaker

from src.constants import CONN_STRING
from src.database_model import Item, BASE

LOGGER = logging.getLogger(__name__)


class ScrapyHandler:
    """ handler class collecting output of scraping and implementing methods for persisting output into database """
    _page_content: List[Dict[str, List[Item]]] = []

    # database engine
    engine = sqlalchemy.create_engine(CONN_STRING)
    BASE.metadata.create_all(engine)  # database init
    session = sessionmaker(bind=engine)()  # create session

    @classmethod
    def push_to_database(cls):
        """ this method saves entire output stored in _page_content attribute to database """
        ordered_content = sorted(cls._page_content, key=lambda x: next(iter(x)))
        for page_content in ordered_content:
            page = next(iter(page_content))
            LOGGER.info(f'adding page {page} to database')
            for index, item in enumerate(page_content[page], start=1):
                LOGGER.info(f'\tadding item {index} to database')
                cls.session.add(item)
            cls.session.flush()
            cls.session.commit()
        cls.session.close()
        cls.engine.dispose()

    @classmethod
    def add_content(cls, item_dict: Dict[str, List[Item]]):
        cls._page_content.append(item_dict)


class SRealitySpider(scrapy.Spider):
    """ Main crawling class used for scraping content of sreality flat ads
     It retrieves first 500 elements (title and image) from sreality flat ads and save them to 'items' table in
     local postgresql database 'postgres'
     """
    name = 'sreality'
    allowed_domains = ['sreality.cz']

    def start_requests(self):
        """ Each page contains 20 records, we crawl first 25 pages in order to get first 500 records
         (this could be done more thorough, nevertheless this is the fastest way)"""
        for page in range(1, 26):
            yield scrapy.Request(f'https://www.sreality.cz/hledani/prodej/byty?strana={page}')

    def parse(self, response):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--headless')

        browser = webdriver.Chrome('/chromedriver', chrome_options=chrome_options)

        url = response.request.url
        current_page = int(url.split('=')[-1])
        browser.get(url)

        innerHTML = browser.execute_script("return document.body.innerHTML")
        soup = BeautifulSoup(innerHTML, 'html.parser')
        titles = [elem.text.replace('\xa0', ' ') for elem in soup.find_all(class_="name ng-binding")]
        image_urls = [image.select('preact img')[0]['src'] for image
                      in soup.find_all(class_="property ng-scope")]  # get image urls

        ScrapyHandler.add_content(self.generate_items(current_page, titles=titles, image_urls=image_urls))
        yield {'page': current_page, 'titles': titles, 'image_urls': image_urls}
        browser.close()

    @staticmethod
    def generate_items(page, titles, image_urls) -> Dict[str, List[Item]]:
        items: List[Item] = []
        assert len(titles) == len(image_urls), \
            f'Unable to fetch a complete item, there are missing images or titles'
        for title, image_url in zip(titles, image_urls):
            items.append(Item(title=title, image=image_url))
        return {page: items}


def run_scrapy():
    """ helper runnner to run crawling process and push results to postgresql database """
    process = CrawlerProcess()
    process.crawl(SRealitySpider)
    process.start()
    ScrapyHandler.push_to_database()
