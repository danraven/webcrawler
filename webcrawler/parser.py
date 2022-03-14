from abc import ABC, abstractmethod
from typing import Generator
from dataclasses import dataclass
from webcrawler.urlcollector import ProcessedUrl
import re


@dataclass
class Item:
    url: str


@dataclass
class OdaProduct(Item):
    name: str
    category: list[str]
    price: float
    currency: str
    description: str
    unit_price: float
    unit: str


class Parser(ABC):
    @abstractmethod(callable)
    def parse(processed_url: ProcessedUrl) -> Generator[Item, None, None]:
        pass


class OdaProductParser(Parser):
    def __init__(self):
        self.up_pattern = re.compile(r'.+ (\d+)[\.,](\d+) per (\s+)')

    def parse(
        self,
        processed_url: ProcessedUrl
    ) -> Generator[OdaProduct, None, None]:
        url, html = processed_url
        details = html.find('div', class_='product-detail')
        category = [li.get_text() for li in details.ol.find_all('li')]
        name = details.h1.get_text()
        description = details.find('div', class_='description').get_text()
        price_box = details.find('div', itemprop='price')
        price = float(price_box['content'])
        currency = price_box.find('span', itemProp='priceCurrency')['content']
        up_box = details.find('div', class_='unit-price')
        up_match = self.up_pattern.search(up_box.get_text())

        yield OdaProduct(
            url,
            name,
            category,
            price,
            currency,
            description,
            float('{}.{}'.format(up_match.group(1), up_match.group(2))),
            up_match.group(3)
        )
