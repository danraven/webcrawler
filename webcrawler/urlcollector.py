from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
from typing import Generator, NamedTuple, Optional
from urllib.robotparser import RobotFileParser
from urllib.error import URLError
from webcrawler.http import parse_html
import logging
import re


CollectedUrl = NamedTuple('CollectedUrl', [('url', str), ('hit', bool)])
ProcessedUrl = NamedTuple('ProcessedUrl', [
    ('url', str),
    ('html', Optional[BeautifulSoup])
])

CollectorGenerator = Generator[CollectedUrl, ProcessedUrl, None]


class UrlCollector(ABC):
    def __init__(
        self,
        base_url: str,
        target_pattern: str,
        logger: logging.Logger = logging,
        **kwargs
    ):
        self.base_url = base_url.strip('/') + '/'
        self.target_pattern = re.compile(target_pattern)
        self.logger = logger
        self.collector = self._init_collector()
        self.found_urls = []

    def collect(self) -> Generator[ProcessedUrl, None, None]:
        """
        Initiates URL collection returning a generator supplying
        a namedtuple containing the matched address and the parsed
        HTML content.
        """
        c: CollectedUrl = self.collector.send(None)
        try:
            while True:
                if c.url in self.found_urls:
                    self.logger.debug(
                        'Skipping already hit URL: %s',
                        c.url
                    )
                    c = self.collector.send(ProcessedUrl(c.url, None))
                    continue
                self.found_urls.append(c.url)
                try:
                    soup = parse_html(c.url)
                except URLError as err:
                    self.logger.warn('Unable to parse URL: %s', err)
                    c = self.collector.send(ProcessedUrl(c.url, None))
                    continue
                processed = ProcessedUrl(c.url, soup)
                if c.hit:
                    self.logger.debug('URL hit: %s', c.url)
                    yield processed
                c = self.collector.send(processed)
        except StopIteration:
            pass

    @abstractmethod
    def _init_collector(self) -> CollectorGenerator:
        pass


class SitemapCollector(UrlCollector):
    """
    A collector that parses the sitemap of the website recursively,
    and yields URLs that match the supplied pattern.

    base_url: str
        The base URL of the website
    sitemap_path: str
        Path to the sitemap relative to base_url
    target_pattern: str
        A regexp string to be used to match URLs to be parsed
    logger: Logger
        Logger instance to be used for debugging
    """
    def __init__(
        self,
        base_url: str,
        sitemap_path: str,
        target_pattern: str,
        logger: logging.Logger = logging
    ):
        self.sitemap_path = sitemap_path.strip('/')
        super().__init__(base_url, target_pattern, logger)

    def _init_collector(self) -> CollectorGenerator:
        return self._get_sitemap_generator(
            self.base_url + self.sitemap_path
        )

    def _get_sitemap_generator(self, sitemap_url: str) -> CollectorGenerator:
        self.logger.debug('Parsing sitemap: %s', sitemap_url)

        try:
            soup = parse_html(sitemap_url)
        except URLError as err:
            self.logger.error('Could not parse sitemap: %s', err)

        for submap in soup.find_all('sitemap'):
            self.logger.debug('Sitemap found: %s', submap.loc.text)
            yield from self._get_sitemap_generator(submap.loc.text)
        for url in soup.find_all('url'):
            location = url.loc.text
            if self.target_pattern.search(location) is None:
                continue
            self.logger.debug('Matched URL from sitemap: %s', location)
            yield CollectedUrl(location, True)


class RobotsTxtCollector(SitemapCollector):
    """
    A collector that parses the robots.txt of the website and
    attempts to fetch its sitemaps. Extension of SitemapCollector
    and calls its generator internally after obtaining the sitemaps.

    base_url: str
        The base URL of the website
    target_pattern: str
        A regexp string to be used to match URLs to be parsed
    robots_path: str
        The path to robots.txt relative to base_url (defaults to robots.txt)
    logger: Logger
        Logger instance to be used for debugging
    """
    def __init__(
        self,
        base_url: str,
        target_pattern: str,
        robots_path: str = 'robots.txt',
        logger: logging.Logger = logging
    ):
        self.robots_path = robots_path.strip('/')
        super().__init__(base_url, '', target_pattern, logger)

    def _init_collector(self) -> CollectorGenerator:
        parser = RobotFileParser(self.base_url + self.robots_path)
        parser.read()
        for sitemap_url in parser.site_maps():
            self.logger.debug('Sitemap found: %s', sitemap_url)
            yield from self._get_sitemap_generator(sitemap_url)


class CrawlCollector(UrlCollector):
    """
    A collector that attempts to crawl through the entire website
    in order to fetch the URLs that match the supplied pattern.
    Takes advantage of the generator's send() method to receive
    a fetched and parsed HTML of a page in order to sweep through
    URLs.

    base_url: str
        The base URL of the site.
    target_pattern: str
        A regexp string to be used to match URLs to be parsed
    crawl_pattern: str
        Additional pattern that will render the target for crawling
        purposes if matched, without being considered a match to be
        further parsed.
    start_path: str
        Path relative to base_url the crawler starts with.
    logger: Logger
        Logger instance to be used for debugging
    """
    def __init__(
        self,
        base_url: str,
        target_pattern: str,
        crawl_pattern: str,
        start_path: str = '',
        logger: logging.Logger = logging,
        **kwargs
    ):
        self.start_path = start_path.lstrip('/')
        self.crawl_pattern = re.compile(crawl_pattern)
        super().__init__(base_url, target_pattern, logger)

    def _init_collector(self) -> CollectorGenerator:
        return self._get_crawl_generator(self.base_url + self.start_path)

    def _get_crawl_generator(self, crawl_url) -> CollectorGenerator:
        self.logger.debug('Crawling URL: %s', crawl_url)
        processed = yield CollectedUrl(
            crawl_url,
            bool(self.target_pattern.search(crawl_url))
        )

        if not processed.html:
            return

        links = (processed.html.find_all('a', href=self.target_pattern)
                 + processed.html.find_all('a', href=self.crawl_pattern))

        for link in links:
            href = self._format_href(link.get('href'))
            if not href:
                continue
            yield from self._get_crawl_generator(href)

    def _format_href(self, href: str) -> Optional[str]:
        if href.startswith('/'):
            return self.base_url + href.lstrip('/')
        elif href.startswith(self.base_url):
            return href
        return None
