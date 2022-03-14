from bs4 import BeautifulSoup
from typing import Generator
from urllib.robotparser import RobotFileParser
from urllib import request
import logging
import re


def sitemap_collector(
    sitemap_url: str,
    pattern: str
) -> Generator[str, BeautifulSoup, None]:
    logging.debug('Parsing sitemap: %s', sitemap_url)
    regexp = re.compile(pattern)
    r = request.urlopen(sitemap_url).read()
    soup = BeautifulSoup(r, 'lxml')
    for submap in soup.find_all('sitemap'):
        logging.debug('Sitemap found: %s', submap.loc.text)
        yield from sitemap_collector(submap.loc.text, pattern)
    for url in soup.find_all('url'):
        location = url.loc.text
        if regexp.search(location) is None:
            continue
        logging.debug('Matched URL from sitemap: %s', location)
        yield location


def robotstxt_collector(
    base_url: str,
    pattern: str
) -> Generator[str, BeautifulSoup, None]:
    parser = RobotFileParser(base_url.strip('/') + '/robots.txt')
    parser.read()
    for sitemap_url in parser.site_maps():
        logging.debug('Sitemap found: %s', sitemap_url)
        yield from sitemap_collector(sitemap_url, pattern)


def crawl_collector(
    target_url: str,
    base_url: str,
    pattern: str,
    crawl_patterns: list[str],
    hits: list = []
) -> Generator[str, BeautifulSoup, list]:
    full_url = base_url.strip('/') + target_url
    logging.debug('Checking possible URL: %s', full_url)
    if target_url in hits:
        logging.debug('URL already hit, skipping: %s', full_url)
        return hits

    hits.append(target_url)

    target_regexp = re.compile(pattern)
    crawl_regexp = re.compile('|'.join(crawl_patterns))

    if target_regexp.search(target_url):
        logging.debug('Matched URL from crawled page: %s', full_url)
        soup = yield full_url
    else:
        logging.debug('Parsing URL for possible links: %s', full_url)
        r = request.urlopen(full_url).read()
        soup = BeautifulSoup(r, 'lxml')

    for hit in soup.find_all('a', href=target_regexp):
        logging.debug('Found possible match: %s', hit.get('href'))
        hits = yield from crawl_collector(
            hit.get('href'),
            base_url,
            pattern,
            crawl_patterns,
            hits
        )

    for link in soup.find_all('a', href=crawl_regexp):
        logging.debug('Found crawlable URL: %s', link.get('href'))
        hits = yield from crawl_collector(
            link.get('href'),
            base_url,
            pattern,
            crawl_patterns,
            hits
        )
    return hits
