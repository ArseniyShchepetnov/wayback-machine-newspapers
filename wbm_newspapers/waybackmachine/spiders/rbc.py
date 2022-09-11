"""Scraper for rbc.ru site from waybackmachine."""
import logging

from bs4 import BeautifulSoup
from scrapy.utils.log import configure_logging

from wbm_newspapers.domains.rbc.extract import RbcExtractor
from wbm_newspapers.extraction.extraction import BaseExtractor
from wbm_newspapers.waybackmachine.spiders.base import SpiderWaybackMachineBase

configure_logging(install_root_handler=False)

logger = logging.getLogger(__name__)
logger_handler = logging.FileHandler("spider_rbc.log",
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
