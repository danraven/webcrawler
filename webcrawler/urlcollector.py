from bs4 import BeautifulSoup
from typing import Generator
from urllib.robotparser import RobotFileParser
from urllib.error import URLError
from webcrawler.http import parse_html
import enum
import logging
import re

class CollectorType(enum.Enum):
    ROBOTSTXT = 'robotstxt_collector'
    SITEMAP = 'sitemap_collector'
    CRAWL = 'crawl_collector'

class UrlCollector:
    def __init__(
        self,
        base_url: str,
        target_pattern: str,
        collector_type: CollectorType,
        logger: logging.Logger = logging,
        **kwargs
    ):
        self.base_url = base_url
        self.target_pattern = re.compile(target_pattern)
        self.collector = self._init_collector(collector_type, **kwargs)
        self.logger = logger
        self.found_urls = []


def sitemap_collector(
    sitemap_url: str,
    pattern: str,
    logger: logging.Logger = logging
) -> Generator[str, BeautifulSoup, None]:
    logging.debug('Parsing sitemap: %s', sitemap_url)
    regexp = re.compile(pattern)

    try:
        soup = parse_html(sitemap_url)
    except URLError as err:
        logger.error('Could not parse sitemap: %s', err)

    for submap in soup.find_all('sitemap'):
        logger.debug('Sitemap found: %s', submap.loc.text)
        yield from sitemap_collector(submap.loc.text, pattern, logger)
    for url in soup.find_all('url'):
        location = url.loc.text
        if regexp.search(location) is None:
            continue
        logger.debug('Matched URL from sitemap: %s', location)
        yield location


def robotstxt_collector(
    base_url: str,
    pattern: str,
    logger: logging.Logger = logging
) -> Generator[str, BeautifulSoup, None]:
    parser = RobotFileParser(base_url.strip('/') + '/robots.txt')
    parser.read()
    for sitemap_url in parser.site_maps():
        logger.debug('Sitemap found: %s', sitemap_url)
        yield from sitemap_collector(sitemap_url, pattern, logger)


def crawl_collector(
    target_url: str,
    base_url: str,
    pattern: str,
    crawl_patterns: list[str],
    hits: list = [],
    logger: logging.Logger = logging
) -> Generator[str, BeautifulSoup, list]:
    full_url = base_url.strip('/') + target_url
    logger.debug('Checking possible URL: %s', full_url)
    if target_url in hits:
        logger.debug('URL already hit, skipping: %s', full_url)
        return hits

    hits.append(target_url)

    target_regexp = re.compile(pattern)
    crawl_regexp = re.compile('|'.join(crawl_patterns))

    if target_regexp.search(target_url):
        logger.debug('Matched URL from crawled page: %s', full_url)
        soup = yield full_url
    else:
        logger.debug('Parsing URL for possible links: %s', full_url)
        try:
            soup = parse_html(full_url)
        except URLError as err:
            logger.warn('Could not parse URL: %s', err)

    for hit in soup.find_all('a', href=target_regexp):
        logger.debug('Found possible match: %s', hit.get('href'))
        hits = yield from crawl_collector(
            hit.get('href'),
            base_url,
            pattern,
            crawl_patterns,
            hits,
            logger
        )

    for link in soup.find_all('a', href=crawl_regexp):
        logger.debug('Found crawlable URL: %s', link.get('href'))
        hits = yield from crawl_collector(
            link.get('href'),
            base_url,
            pattern,
            crawl_patterns,
            hits,
            logger
        )
    return hits
