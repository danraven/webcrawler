from webcrawler.urlcollector import UrlCollector
from webcrawler.parser import Parser
from webcrawler.output import Output
from webcrawler.config import Config
from importlib import import_module
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

    @classmethod
    def from_config(cls, conf: Config):
        CollectorClass = get_conf_class(
            conf.url_collector_config.classname
        )
        OutputClass = get_conf_class(conf.output_config.classname)
        ParserClass = get_conf_class(conf.parser_config.classname)

        assert issubclass(CollectorClass, UrlCollector)
        assert issubclass(ParserClass, Parser)
        assert issubclass(OutputClass, Output)

        logger = logging.getLogger(conf.log_name)
        logger.setLevel(conf.log_level)
        logger.addHandler(logging.StreamHandler())

        return cls(
            CollectorClass(logger=logger, **conf.url_collector_config.options),
            ParserClass(**conf.parser_config.options),
            OutputClass(logger=logger, **conf.output_config.options),
            conf.limit,
            conf.delay,
            logger
        )

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


def get_conf_class(classname):
    parts = classname.split('.')
    return getattr(import_module('.'.join(parts[:-1])), parts[-1])
