"""Meduza site scraping."""
import logging
import os
import re
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from anynews_wbm.domains.meduza.extract import MeduzaExtractor
from anynews_wbm.extaction.utils import path_stat
from anynews_wbm.snapshot.db.client import DbClient, SnapshotCollectionClient
from anynews_wbm.waybackmachine.items import WaybackMachineGeneralArticleItem
from anynews_wbm.waybackmachine.spiders.base import (SpiderWaybackMachineBase,
                                                     WaybackMachineResponseCDX)
from bs4 import BeautifulSoup
from scrapy.utils.log import configure_logging

configure_logging(install_root_handler=False)

logger = logging.getLogger(__name__)
logger_handler = logging.FileHandler("spider_meduza.log",
                                     encoding='utf-8',
                                     mode="w")
logger_handler.setFormatter(logging.Formatter(
    "%(name)s:%(levelname)s:%(message)s"))
logger.addHandler(logger_handler)


class SpiderMeduza(SpiderWaybackMachineBase):
    CONNECTION = 'mongodb://localhost'
    DATABASE = 'anynews_wbm'
    name = "spider_meduza"

    def __init__(self, *args, **kwargs):
        SpiderWaybackMachineBase.__init__(self, *args, **kwargs)

        self.client = None
        self.collection = None

        filter_original = self.special_settings().get('filter_original')
        if filter_original is not None and filter_original:
            self.client = DbClient(connection=self.CONNECTION,
                                   database=self.DATABASE)
            self.collection = SnapshotCollectionClient(self.client, self.name)

    def filter(self,
               data: WaybackMachineResponseCDX) -> WaybackMachineResponseCDX:
        """Filter urls."""
        def _filter_original(original: str) -> bool:
            return len(self.collection.find_original_url(original)) == 0

        if self.collection is not None:
            n_rows_before = data.n_rows
            data = data.filter(lambda row: _filter_original(row['original']))
            logger.info("Spider '%s' filtered %d rows by original URL %d left",
                        self.name, n_rows_before - data.n_rows, data.n_rows)
        logger.info("Path statistics\n%s", path_stat(data.data['original']))
        return data

    def parse(self, response):
        """Parse response."""

        soup = BeautifulSoup(response.text)
        url_pars = WaybackMachineResponseCDX.from_archive_url(response.url)
        url_original = url_pars['original']

        try:
            extractor = MeduzaExtractor(soup, url_original)
        except ValueError as err:
            logger.error("%s", str(err))
            raise err

        logger.debug("Processing... '%s'", url_original)

        text = extractor.get_text()
        title = extractor.get_title()

        if len(text) > 0 and len(title) == 0:
            logger.error("Title length is zero for url '%s'. Text length = %d",
                         response.url, len(text))
            raise ValueError(
                f"Title length is zero. Text length = {len(text)}")

        if len(text) > 0:

            url_datetime = extractor.get_datetime()
            if url_datetime is not None:
                url_date = url_datetime.isoformat()
            else:
                url_date = ''
            title_date = extractor.get_header_datetime()

            logger.debug("stat: text = %d, title = %d, "
                         "title_date = %d, url_date = %d",
                         len(text), len(title), len(title_date), len(url_date))

            item = WaybackMachineGeneralArticleItem(
                text=text,
                title=title,
                publish_date='',
                title_date=title_date,
                url_date=url_date,
                url=response.url,
                timestamp=url_pars['timestamp'],
                original=url_original,
                snapshot=response.text,
                path="?"
            )

        else:
            if title:
                logger.warning(
                    "Warning while retrieving title no text found. "
                    "Title='%s' url='%s'",
                    title, response.url)
            logger.info("No text found: '%s'", response.url)
            item = None

        logger.debug("End processing.")
        return item


def url2path(url: str) -> str:

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
