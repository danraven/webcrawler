import logging
from webcrawler.urlcollector import CrawlCollector
from webcrawler.parser import OdaProductParser
from webcrawler.output import LogOutput
from webcrawler.runner import Runner


def run():
    logging.basicConfig(level=logging.INFO)
    pattern = r'^.+\/products\/\d+\-[^\/]+\/$'
    targets = [
        r'\/products\/',
        r'\/categories\/\d+\-[^\/]+\/$'
    ]
    collector = CrawlCollector(
        'https://oda.com/',
        pattern,
        '|'.join(targets)
    )
    output = LogOutput(logging)
    parser = OdaProductParser()

    runner = Runner(
        collector,
        parser,
        output,
        15,
        0
    )

    runner.run()


if __name__ == '__main__':
    run()
