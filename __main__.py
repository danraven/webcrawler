import logging
from webcrawler.urlcollector import UrlCollector, CollectorType
from webcrawler.parser import OdaProductParser
from webcrawler.output import LogOutput
from webcrawler.runner import Runner


def run():
    logger = logging.Logger('webcrawler', level=logging.INFO)
    pattern = r'^.+\/products\/\d+\-[^\/]+\/$'
    collector = UrlCollector(
        'https://oda.com/',
        pattern,
        CollectorType.ROBOTSTXT,
        logger=logger
    )
    output = LogOutput(logger)
    parser = OdaProductParser()

    runner = Runner(
        collector,
        parser,
        output,
        15,
        0,
        logger
    )

    runner.run()


if __name__ == '__main__':
    run()
