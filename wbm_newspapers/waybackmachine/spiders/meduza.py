"""Meduza site scraping."""
import logging

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
