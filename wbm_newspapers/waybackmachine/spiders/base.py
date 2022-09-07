"""Wayback Machine CDX spider."""
import abc
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Pattern

import scrapy
import yaml
from bs4 import BeautifulSoup
from waybackmachine_cdx import WaybackMachineCDX

from wbm_newspapers.extraction.extraction import BaseExtractor
from wbm_newspapers.waybackmachine import settings
from wbm_newspapers.waybackmachine.items import \
    WaybackMachineGeneralArticleItem
from wbm_newspapers.waybackmachine.spiders.db import SpiderDatabase
from wbm_newspapers.waybackmachine.spiders.response import \
    WaybackMachineResponseCDX

logger = logging.getLogger(__name__)


class DefaultFilter:
    """Filter."""

    def __init__(self,
                 include_url: Optional[List[str]] = None,
                 exclude_url: Optional[List[str]] = None,
                 exclude_statuscodes: Optional[List[str]] = None,
                 include_mimetypes: Optional[List[str]] = None):

        include_url_ = None
        exclude_url_ = None

        if include_url is not None:
            include_url_ = [re.compile(exp) for exp in include_url]

        if exclude_url is not None:
            exclude_url_ = [re.compile(exp) for exp in exclude_url]

        if exclude_statuscodes is None:
            exclude_statuscodes = ['404']

        self._exclude_url = exclude_url_
        self._include_url = include_url_

        self._exclude_statuscodes = exclude_statuscodes
        self._include_mimetypes = include_mimetypes

    @staticmethod
    def _is_in_list(value: str, exp_list: List[Pattern]) -> bool:
        result = any(exp.fullmatch(value) is not None for exp in exp_list)
        return result

    def filter_statuscode(self, statuscode: str) -> bool:
        """Filter statuscodes"""
        return statuscode not in self._exclude_statuscodes

    def filter_url(self, url: str) -> bool:
        """"Filter by URL"""

        if self._include_url is None or len(self._include_url) == 0:
            inc = True
        else:
            inc = self._is_in_list(url, self._include_url)

        if self._exclude_url is None or len(self._exclude_url) == 0:
            not_exc = True
        else:
            not_exc = not self._is_in_list(url, self._exclude_url)

        return inc and not_exc

    def filter_mimetype(self, mimetype: str) -> bool:
        """Mimetypes filtering"""
        if self._include_mimetypes is None:
            inc = True
        else:
            inc = mimetype in self._include_mimetypes
        return inc


class SpiderWaybackMachineBase(scrapy.Spider, metaclass=abc.ABCMeta):
    """Basic Wayback Machine domain scraper."""

    DB_HOST = 'mongodb://localhost'
    DB_NAME = 'anynews_wbm'

    counter = {'parse': 0, 'success': 0, 'failed': 0}

    def __init__(self,
                 *args,
                 settings_file: str,
                 clear: str = 'False',
                 **kwargs):

        super().__init__(*args, **kwargs)

        self.output_directory = settings.data_dir
        scraper_settings = self.read_setting_file(settings_file)
        cdx_settings = scraper_settings['cdx']

        for dt_item in ['from_dt', 'to_dt']:
            if dt_item in cdx_settings.keys():
                cdx_settings[dt_item] = datetime.strptime(
                    cdx_settings[dt_item],
                    "%Y-%m-%d %H:%M:%S"
                )

        self._cdx = WaybackMachineCDX(**cdx_settings)
        self._filter = DefaultFilter(**scraper_settings['filter'])
        self.clear_database: bool = clear.lower() in ['true', 't', 'y', 'yes']
        logger.info("Collection will be dropped: %s", clear)
        self._special_settings = scraper_settings

        filter_original = self.special_settings().get('filter_original')
        enable_mongodb = self.special_settings().get('enable_mongodb', True)

        self._db: Optional[SpiderDatabase] = None
        if filter_original is not None and filter_original and enable_mongodb:
            db_settings = self.special_settings().get('db', {})
            self._db = SpiderDatabase(
                self.name,
                db_settings.get('host', self.DB_HOST),
                db_settings.get('database', self.DB_NAME))

    def special_settings(self) -> Dict[str, Any]:
        """Special spider settings from file."""
        return self._special_settings

    def read_setting_file(self, file: str) -> Dict:
        """Read YAML file with settings and return dict."""

        logger.info("read config file for spider '%s': '%s'", self.name, file)
        with open(file, 'r', encoding='utf-8') as stream:
            data = yaml.safe_load(stream)

        return data

    def start_requests(self):
        """Starting request."""

        self._cdx.set_output_format('json')
        self._cdx.set_resume_key(show=True)

        request = scrapy.Request(self._cdx.cdx, self.parse_cdx)

        yield request

    def _filter_cdx_response(self,
                             data: 'WaybackMachineResponseCDX') \
            -> 'WaybackMachineResponseCDX':

        logging.info("CDX response %d rows.", data.n_rows)

        data = data.filter(
            lambda row: self._filter.filter_statuscode(row['statuscode']))
        logging.info("CDX response %d rows after status filtering.",
                     data.n_rows)

        data = data.filter(
            lambda row: self._filter.filter_mimetype(row['mimetype']))
        logging.info("CDX response %d rows after mimetype filtering.",
                     data.n_rows)

        data = data.filter(
            lambda row: self._filter.filter_url(row['original']))
        logging.info("CDX response %d rows after URL filtering.",
                     data.n_rows)

        return data

    def filter(self,
               data: WaybackMachineResponseCDX) -> WaybackMachineResponseCDX:
        """Filter urls."""
        if self._db is not None:
            n_rows_before = data.n_rows
            self._db.filter(data)
            logger.info("Spider '%s' filtered %d rows by original URL %d left",
                        self.name, n_rows_before - data.n_rows, data.n_rows)
        return data

    def parse_cdx(self, response: scrapy.http.TextResponse):
        """Parse cdx responses."""

        data = WaybackMachineResponseCDX.from_text(response.text)

        data = self._filter_cdx_response(data)
        data = self.filter(data)

        snapshots_iter = SnapshotUrlIterator(data)
        logger.info("Number of urls to process = %d", len(snapshots_iter))
        for index, url in enumerate(snapshots_iter):
            if index % 100 == 0:
                logger.debug("Progress: %f2.2; Current: %d; All: %d",
                             index / len(snapshots_iter),
                             index,
                             len(snapshots_iter))
                logger.debug("Counter: %s", self.counter)
            yield scrapy.Request(url, self.parse)

        logger.info("Counter: %s", self.counter)

        if data.resume_key is not None:

            self._cdx.set_resume_key(show=True, key=data.resume_key)
            request = scrapy.Request(self._cdx.cdx, self.parse_cdx)

            yield request

        else:
            logger.info("No resume key was provided. Finalizing...")

    @abc.abstractmethod
    def get_extractor(self, soup: BeautifulSoup, url: str) -> BaseExtractor:
        """Parse snapshot"""

    def parse(self, response, *args, **kwargs):  # pylint: disable=unused-argument
        """Parse snapshot"""

        self.counter['parse'] += 1

        soup = BeautifulSoup(response.text, features="lxml")
        url_pars = WaybackMachineResponseCDX.from_archive_url(response.url)
        url_original = url_pars['original']

        extractor = self.get_extractor(soup, url_original)

        logger.debug("Processing... '%s'", url_original)

        text = extractor.get_text()
        title = extractor.get_title()
        summary = extractor.get_summary()

        if len(text) > 0 and len(title) == 0:
            logger.error("Title length is zero for url '%s'. Text length = %d",
                         response.url, len(text))
            self.counter['failed'] += 1
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
                summary=summary,
                publish_date='',
                title_date=title_date,
                url_date=url_date,
                url=response.url,
                timestamp=url_pars['timestamp'],
                original=url_original,
                snapshot=response.text,
                path="?"
            )
            self.counter['success'] += 1
        else:
            if title:
                logger.warning(
                    "Warning while retrieving title no text found. "
                    "Title='%s' url='%s'",
                    title, response.url)
            logger.info("No text found: '%s'", response.url)
            item = None
            self.counter['failed'] += 1

        logger.debug("End processing.")
        return item


class SnapshotUrlIterator:
    """Iterator over snapshot urls."""

    def __init__(self, cdx_data: WaybackMachineResponseCDX):

        self._data = cdx_data
        self._index = 0

    def __iter__(self):
        return self

    def __len__(self) -> int:
        return self._data.n_rows

    def __next__(self):

        if self._index < len(self):
            row = self._data.data.iloc[self._index]
            snapshot = row.to_dict()

            url = self._data.snapshot_to_archive_url(snapshot)
            self._index += 1
        else:
            raise StopIteration

        return url
