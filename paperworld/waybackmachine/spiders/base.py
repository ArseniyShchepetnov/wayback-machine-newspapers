"""Wayback Machine CDX spider."""
import abc
import json
import logging
import os
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import re
import pandas as pd
import parse
import scrapy
import yaml
from paperworld.cdx import WaybackMachineCDX
from paperworld.waybackmachine import settings

logger = logging.getLogger(__name__)


class DefaultFilter:

    def __init__(self,
                 include_url: Optional[List[str]] = None,
                 exclude_url: Optional[List[str]] = None,
                 exclude_statuscodes: Optional[List[str]] = None,
                 include_mimetypes: Optional[List[str]] = None):

        if include_url is not None:
            self._include_url = [re.compile(exp) for exp in include_url]
        else:
            self._include_url = None

        if exclude_url is not None:
            self._exclude_url = [re.compile(exp) for exp in exclude_url]
        else:
            self._exclude_url = None

        if exclude_statuscodes is None:
            exclude_statuscodes = ['404']

        self._exclude_statuscodes = exclude_statuscodes
        self._include_mimetypes = include_mimetypes

    @staticmethod
    def _is_in_list(value: str, exp_list: List[str]) -> bool:
        result = any([exp.fullmatch(value) is not None for exp in exp_list])
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

    def __init__(self,
                 *args,
                 settings_file: str,
                 **kwargs):

        super().__init__(*args, **kwargs)

        self.output_directory = settings.data_dir

        scraper_settings = self.read_setting_file(settings_file)

        self._init_output_dir(scraper_settings)

        cdx_settings = scraper_settings['cdx']
        for dt in ['from_dt', 'to_dt']:
            if dt in cdx_settings.keys():
                cdx_settings[dt] = datetime.strptime(cdx_settings[dt],
                                                     "%Y-%m-%d %H:%M:%S")

        self._cdx = WaybackMachineCDX(**cdx_settings)

        self._filter = DefaultFilter(**scraper_settings['filter'])

    @property
    def scraper_outdir(self) -> str:
        return os.path.join(self.output_directory, self.name)

    def _init_output_dir(self, scraper_settings: Dict[str, Any]):
        if os.path.exists(self.scraper_outdir):
            dir2remove = os.path.join(self.output_directory,
                                      self.scraper_outdir)
            shutil.rmtree(dir2remove)

        os.makedirs(self.scraper_outdir)

        filename = os.path.join(self.scraper_outdir, 'inputs.json')
        with open(filename, "w") as fobj:
            json.dump(scraper_settings, fobj, indent=4)

        filename = os.path.join(self.scraper_outdir, 'name')
        with open(filename, "w") as fobj:
            fobj.write(self.name)

    def read_setting_file(self, file: str) -> Dict:
        """Read YAML file with settings and return dict."""

        logger.info("read config file for spider '%s': '%s'", self.name, file)
        with open(file, 'r') as stream:
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

    def parse_cdx(self, response: scrapy.http.TextResponse):
        """Parse cdx responses."""

        data = WaybackMachineResponseCDX.from_text(response.text)

        data = self._filter_cdx_response(data)

        for url in SnapshotUrlIterator(data):
            yield scrapy.Request(url, self.parse)

        if data.resume_key is not None:

            self._cdx.set_resume_key(show=True, key=data.resume_key)
            request = scrapy.Request(self._cdx.cdx, self.parse_cdx)

            yield request

    @abc.abstractmethod
    def parse(self, response: scrapy.http.TextResponse):  # pylint: disable=arguments-differ
        """Parse snapshot"""


class WaybackMachineResponseCDX:
    """CDX response data."""

    url_template = 'https://web.archive.org/web/{timestamp}/{original}'

    def __init__(self, data: pd.DataFrame, resume_key: str):
        """Parse response"""

        self._resume_key = resume_key
        self._data = data

    @classmethod
    def from_list(cls, data: List[List[str]]) -> 'WaybackMachineResponseCDX':
        """Instantiate class form list of lists data."""

        if len(data[-2]) == 0:

            resume_key = data[-1][0]
            data = pd.DataFrame(data[1:-2], columns=data[0])

        else:

            resume_key = None
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


class SnapshotUrlIterator:
    """Iterator over snapshot urls."""

    def __init__(self, cdx_data: WaybackMachineResponseCDX):

        self._data = cdx_data
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):

        if self._index < self._data.data.shape[0]:
            row = self._data.data.iloc[self._index]
            snapshot = row.to_dict()

            url = self._data.snapshot_to_archive_url(snapshot)
            self._index += 1
        else:
            raise StopIteration

        return url
