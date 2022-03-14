import logging
from urlcollector import crawl_collector
from bs4 import BeautifulSoup
from urllib import request


def run():
    logging.basicConfig(format='%(message)s', level=logging.DEBUG)
    limit = 10
    pattern = r'^.+\/products\/\d+\-[^\/]+\/$'
    targets = [
        r'\/products\/',
        r'\/categories\/\d+\-[^\/]+\/$'
    ]
    print('Testing crawl collector...\n')
    collector = crawl_collector('/', 'https://oda.com/', pattern, targets)
    url = collector.send(None)
    for i in range(1, limit):
        r = request.urlopen(url).read()
        soup = BeautifulSoup(r, 'lxml')
        url = collector.send(soup)

    print('Done\n')


if __name__ == '__main__':
    run()
