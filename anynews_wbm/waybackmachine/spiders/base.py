"""Wayback Machine CDX spider."""
import abc
from dataclasses import dataclass
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Pattern, Any

import pandas as pd
import parse
import scrapy
import yaml
from anynews_wbm.waybackmachine import settings
from waybackmachine_cdx import WaybackMachineCDX

logger = logging.getLogger(__name__)


class WaybackMachineResponseCDX:
    """CDX response data."""

    url_template = 'https://web.archive.org/web/{timestamp}/{original}'

    def __init__(self, data: pd.DataFrame, resume_key: Optional[str] = None):
        """Parse response"""
        self._resume_key = resume_key
        self._data = data

    @classmethod
    def from_list(cls, data: List[List[str]]) -> 'WaybackMachineResponseCDX':
        """Instantiate class form list of lists data."""

        resume_key: Optional[str] = None
        if len(data[-2]) == 0:
            resume_key = data[-1][0]
            data = pd.DataFrame(data[1:-2], columns=data[0])
        else:
            data = pd.DataFrame(data[1:], columns=data[0])

        return cls(data, resume_key)

    @classmethod
    def from_text(cls, text) -> 'WaybackMachineResponseCDX':
        """From text json response."""
        json_data = json.loads(text)
        return cls.from_list(json_data)

    @property
    def resume_key(self) -> Optional[str]:
        """Resume key parsed from response."""
        return self._resume_key

    @property
    def data(self) -> pd.DataFrame:
        """data."""
        return self._data

    @property
    def columns(self) -> List[str]:
        """Column names."""
        return self._data.columns

    @property
    def n_rows(self):
        """Number of rows in the response."""
        return len(self.data.index)

    def filter(self, condition) -> 'WaybackMachineResponseCDX':
        where = self.data.apply(condition, axis=1)
        data_new = self.data[where]
        return WaybackMachineResponseCDX(data_new, resume_key=self.resume_key)

    @classmethod
    def snapshot_to_archive_url(cls, snapshot: Dict[str, str]) -> str:
        """Get archive url."""
        return cls.url_template.format(**snapshot)

    @classmethod
    def to_archive_url(cls, original: str, timestamp: str) -> str:
        """Get archive url."""
        return cls.url_template.format(original=original, timestamp=timestamp)

    @classmethod
    def from_archive_url(cls, archive_url: str) -> Tuple[str, str]:
        """Get archive url."""
        return parse.parse(cls.url_template, archive_url)


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

    def filter(self,  # pylint: disable=no-self-use
               data: WaybackMachineResponseCDX) -> WaybackMachineResponseCDX:
        """Reimplement this for custom filtration."""
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
    def parse(self, response: scrapy.http.TextResponse):  # pylint: disable=arguments-differ
        """Parse snapshot"""


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
