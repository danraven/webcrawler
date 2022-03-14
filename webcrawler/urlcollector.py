from bs4 import BeautifulSoup
from typing import Generator, NamedTuple, Pattern, Optional
from urllib.robotparser import RobotFileParser
from urllib.error import URLError
from webcrawler.http import parse_html
from functools import partial
import enum
import logging
import re


CollectedUrl = NamedTuple('CollectedUrl', [('url', str), ('hit', bool)])
ProcessedUrl = NamedTuple('ProcessedUrl', [
    ('url', str),
    ('html', Optional[BeautifulSoup])
])


def sitemap_collector(
    sitemap_url: str,
    pattern: Pattern[str],
    logger: logging.Logger = logging
) -> Generator[CollectedUrl, ProcessedUrl, None]:
    """
    A collector that parses the sitemap of the website recursively,
    and yields URLs that match the supplied pattern.

    sitemap_url: str
        The FULL URL to the sitemap xml
    pattern: Pattern
        A compiled Regexp pattern to filter out URLs
    logger: Logger
        Logger instance to be used for debugging
    """
    logger.debug('Parsing sitemap: %s', sitemap_url)

    try:
        soup = parse_html(sitemap_url)
    except URLError as err:
        logger.error('Could not parse sitemap: %s', err)

    for submap in soup.find_all('sitemap'):
        logger.debug('Sitemap found: %s', submap.loc.text)
        yield from sitemap_collector(submap.loc.text, pattern, logger)
    for url in soup.find_all('url'):
        location = url.loc.text
        if pattern.search(location) is None:
            continue
        logger.debug('Matched URL from sitemap: %s', location)
        yield CollectedUrl(location, True)


def robotstxt_collector(
    base_url: str,
    pattern: Pattern[str],
    logger: logging.Logger = logging
) -> Generator[CollectedUrl, ProcessedUrl, None]:
    """
    A collector that parses the robots.txt of the website and
    attempts to fetch its sitemaps. Calls sitemap_collector
    internally.

    base_url: str
        The base URL of the site (without robots.txt appended).
    pattern: Pattern
        A compiled Regexp pattern to filter out URLs
    logger: Logger
        Logger instance to be used for debugging
    """
    parser = RobotFileParser(base_url.rstrip('/') + '/robots.txt')
    parser.read()
    for sitemap_url in parser.site_maps():
        logger.debug('Sitemap found: %s', sitemap_url)
        yield from sitemap_collector(sitemap_url, pattern, logger)


def crawl_collector(
    base_url: str,
    target_path: str,
    pattern: Pattern[str],
    crawl_pattern: Pattern[str],
    logger: logging.Logger = logging
) -> Generator[CollectedUrl, ProcessedUrl, None]:
    """
    A collector that attempts to crawl through the entire website
    in order to fetch the URLs that match the supplied pattern.
    Takes advantage of the generator's send() method to receive
    a fetched and parsed HTML of a page in order to sweep through
    URLs.

    base_url: str
        The base URL of the site.
    target_path: str
        Initial path to start the crawl, relative to base_url
    pattern: Pattern
        A compiled Regexp pattern to filter out URLs
    crawl_pattern: Pattern
        Additional pattern that will render the target for crawling
        purposes if matched, without being considered a match to be
        further parsed.
    logger: Logger
        Logger instance to be used for debugging
    """
    full_url = '{}/{}'.format(
        base_url.rstrip('/'),
        target_path.lstrip('/')
    )
    logger.debug('Checking possible URL: %s', full_url)

    if pattern.search(full_url):
        logger.debug('Matched URL from crawled page: %s', full_url)
        processed = yield CollectedUrl(full_url, True)
    else:
        logger.debug('Parsing URL for possible links: %s', full_url)
        processed = yield CollectedUrl(full_url, False)

    if not processed.html:
        return

    for hit in processed.html.find_all('a', href=pattern):
        logger.debug('Found possible match: %s', hit.get('href'))
        yield from crawl_collector(
            base_url,
            hit.get('href'),
            pattern,
            crawl_pattern,
            logger
        )

    for link in processed.html.find_all('a', href=crawl_pattern):
        logger.debug('Found crawlable URL: %s', link.get('href'))
        yield from crawl_collector(
            base_url,
            link.get('href'),
            pattern,
            crawl_pattern,
            logger
        )


class CollectorType(enum.Enum):
    ROBOTSTXT = partial(robotstxt_collector)
    SITEMAP = partial(sitemap_collector)
    CRAWL = partial(crawl_collector)


class UrlCollector:
    def __init__(
        self,
        base_url: str,
        target_pattern: str,
        collector_type: CollectorType,
        logger: logging.Logger = logging,
        **kwargs
    ):
        self.base_url = base_url.strip('/') + '/'
        self.target_pattern = re.compile(target_pattern)
        self.logger = logger
        self.collector = self._init_collector(collector_type, **kwargs)
        self.found_urls = []

    def collect(self) -> Generator[ProcessedUrl, None, None]:
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

    def _init_collector(
        self,
        collector_type: CollectorType,
        **kwargs
    ) -> Generator[CollectedUrl, ProcessedUrl, None]:
        collector_args = {
            'pattern': self.target_pattern,
            'logger': self.logger
        }

        if collector_type == CollectorType.SITEMAP:
            collector_args['sitemap_url'] = '{}/{}'.format(
                self.base_url,
                kwargs.get('sitemap_path', 'sitemap.xml').strip('/')
            )
        elif collector_type == CollectorType.CRAWL:
            collector_args['base_url'] = self.base_url
            collector_args['target_path'] = kwargs.get('target_path', '/')
            collector_args['crawl_pattern'] = re.compile(
                '|'.join(list(kwargs.get('crawl_pattern', [])))
            )
        elif collector_type == CollectorType.ROBOTSTXT:
            collector_args['base_url'] = self.base_url

        return collector_type.value(**collector_args)
