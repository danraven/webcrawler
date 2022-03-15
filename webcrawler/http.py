from bs4 import BeautifulSoup
from urllib import request
from urllib.error import URLError
from http.client import HTTPResponse


class InvalidResponseError(URLError):
    def __init__(self, message: str, response: HTTPResponse, *args):
        super().__init__(message, *args)
        self.response = response


class InvalidStatusError(InvalidResponseError):
    pass


def parse_html(url: str) -> BeautifulSoup:
    r = request.urlopen(url)
    if int(r.status) != 200:
        raise InvalidStatusError("Invalid status code, expected 200", r)
    return BeautifulSoup(r.read(), "lxml")
