"""Meduza site scraping."""
import logging
import os
import re
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from scrapy.utils.log import configure_logging

from wbm_newspapers.domains.meduza.extract import MeduzaExtractor
from wbm_newspapers.extraction.extraction import BaseExtractor
from wbm_newspapers.waybackmachine.spiders.base import SpiderWaybackMachineBase

configure_logging(install_root_handler=False)

logger = logging.getLogger(__name__)
logger_handler = logging.FileHandler("spider_meduza.log",
                                     encoding='utf-8',
                                     mode="w")
logger_handler.setFormatter(logging.Formatter(
    "%(name)s:%(levelname)s:%(message)s"))
logger.addHandler(logger_handler)


class SpiderMeduza(SpiderWaybackMachineBase):
    """Spider for meduza.io scraping from WaybackMachine."""

    name = "spider_meduza"

    def get_extractor(self, soup: BeautifulSoup, url: str) -> BaseExtractor:
        return MeduzaExtractor(soup, url)


def url2path(url: str) -> str:
    """Convert URL string to path."""
    url_path = urlparse(url).path

    exclude = ['http:', 'https:']
    url_list = url_path.split('/')
    url_list = list(filter(lambda s: len(s) > 0 and s not in exclude,
                           url_list))

    url_list = url_list[1:]
    path = os.path.join(*url_list)

    return path


def get_url_date_iso(url: str) -> Optional[str]:
    """Try to get ISO date from URL."""
    result = None
    match = re.search(r"/\d{4}/\d{2}/\d{2}/", url)
    if match is not None:
        data = match.group()
        date = datetime.strptime(data, r'/%Y/%m/%d/')
        result = date.isoformat()
    return result
