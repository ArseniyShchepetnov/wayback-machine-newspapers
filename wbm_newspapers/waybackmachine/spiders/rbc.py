"""Scraper for rbc.ru site from waybackmachine."""
import logging
import re
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup
from scrapy.utils.log import configure_logging

from wbm_newspapers.domains.rbc.extract import RbcExtractor
from wbm_newspapers.extraction.extraction import BaseExtractor
from wbm_newspapers.waybackmachine.spiders.base import SpiderWaybackMachineBase

configure_logging(install_root_handler=False)

logger = logging.getLogger(__name__)
logger_handler = logging.FileHandler(f"{__name__}.log",
                                     encoding='utf-8',
                                     mode="w")
logger_handler.setFormatter(logging.Formatter(
    "%(name)s:%(levelname)s:%(message)s"))
logger.addHandler(logger_handler)


class SpiderRBC(SpiderWaybackMachineBase):
    """rbc.ru pages parser."""
    CONNECTION = 'mongodb://localhost'
    DATABASE = 'anynews_wbm'
    name = "spider_rbc"

    def get_extractor(self, soup: BeautifulSoup, url: str) -> BaseExtractor:
        return RbcExtractor(soup, url)


def get_url_date_iso(url: str) -> Optional[str]:
    """Try to get ISO date from URL."""
    # pylint: disable=duplicate-code
    result = None
    match = re.search(r"/\d{2}/\d{2}/\d{4}/", url)
    if match is not None:
        data = match.group()
        date = datetime.strptime(data, r'/%d/%m/%Y/')
        result = date.isoformat()
    return result
