import logging
from webcrawler.urlcollector import UrlCollector, CollectorType


def run():
    logging.basicConfig(format='%(message)s', level=logging.INFO)
    pattern = r'^.+\/products\/\d+\-[^\/]+\/$'
    targets = [
        r'\/products\/',
        r'\/categories\/\d+\-[^\/]+\/$'
    ]
    print('Testing crawl collector...\n')
    collector = UrlCollector(
        'https://oda.com/',
        pattern,
        CollectorType.ROBOTSTXT,
    )
    for processed in collector.collect():
        print(processed.url)

    print('Done\n')


if __name__ == '__main__':
    run()
