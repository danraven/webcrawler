from webcrawler.parser import Item
import logging


class Output:
    def start(self) -> None:
        pass

    def add(self, item: Item) -> None:
        pass

    def end(self) -> None:
        pass


class LogOutput(Output):
    def __init__(self, logger: logging.Logger = logging):
        self.logger = logger

    def add(self, item: Item) -> None:
        self.logger.info('%s', item)
