from webcrawler.urlcollector import UrlCollector
from webcrawler.parser import Parser
from webcrawler.output import Output
from time import sleep
import logging


class Runner:
    def __init__(
        self,
        collector: UrlCollector,
        parser: Parser,
        output: Output,
        limit: int = 0,
        delay: int = 0,
        logger: logging.Logger = logging
    ):
        self.collector = collector
        self.parser = parser
        self.output = output
        self.limit = limit
        self.delay = delay / 1000
        self.logger = logger

    def run(self) -> None:
        i = 0
        self.logger.info('Starting runner')
        self.output.start()
        try:
            for url in self.collector.collect():
                if self.limit and i >= self.limit:
                    break
                i = i + 1
                for item in self.parser.parse(url):
                    self.output.add(item)
                if self.delay:
                    sleep(self.delay)
        except Exception as e:
            self.logger.error('Error during crawl, closing output')
            self.output.end()
            raise e
        self.output.end()
        self.logger.info('Runner finished')
