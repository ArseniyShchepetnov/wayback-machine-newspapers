"""Scraper for rbc.ru site from waybackmachine."""
import itertools
import json
import logging
import os
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from src.cdx import WaybackMachineCDX
from src.waybackmachine.items import WaybackMachineGeneralArticleItem
from src.waybackmachine.spiders.base import (SpiderWaybackMachineBase,
                                             WaybackMachineResponseCDX)

logger = logging.getLogger(__file__)


def generate_ignore():
    http = ['http://', 'https://']
    ports = ['', ':80']
    rbc = ['www.rbc.ru', 'rbc.ru']
    slash = ['', '/']

    ignore = []
    for h, r, p, s in itertools.product(http, rbc, ports, slash):
        ignore.append(h + r + p + s)

    return ignore


ignore_list = generate_ignore()
ignore_list.append('https://www.rbc.ru/ajax/')
ignore_list.append('https://www.rbc.ru/advert/')
ignore_list.append('https://www.rbc.ru/politics/')


class SpiderRBC(SpiderWaybackMachineBase):

    name = "spider_rbc"

    def __init__(self,
                 from_datetime: Optional[datetime] = None,
                 to_datetime: Optional[datetime] = None,
                 limit: int = 1000,
                 outdir: str = "~/data/rbc",
                 *args, **kwargs):

        from_datetime = datetime(2019, 1, 1, 0, 0, 0)
        cdx = WaybackMachineCDX('rbc.ru/politics',
                                from_dt=from_datetime,
                                to_dt=to_datetime,
                                limit=limit,
                                matchType='prefix')

        super().__init__(cdx,
                         ignore_statuscode=["404"],
                         ignore_list=ignore_list,
                         *args, **kwargs)

        self.outdir = os.path.expanduser(outdir)

    def parse(self, response):
        """Parse response."""

        soup = BeautifulSoup(response.text)

        tag_text = soup.find("div", {"class": "article__text"})

        if tag_text is not None:

            text = normalize_string(tag_text.text)

            tag_title = soup.find("div", {"class": "article__header__title"})
            title = normalize_string(tag_title.text)

            tag_date = soup.find("span", {"class": "article__header__date"})
            publish_date = tag_date.get('content', '')
            title_date = tag_date.text

            outpath = self.path_from_url(response.url)

            url_pars = WaybackMachineResponseCDX.from_archive_url(response.url)

            item = WaybackMachineGeneralArticleItem(
                text=text,
                title=title,
                publish_date=publish_date,
                title_date=title_date,
                url=response.url,
                timestamp=url_pars['timestamp'],
                original=url_pars['original'],
                path=outpath
            )

            self.save_snapshot(response.text, outpath)

        else:
            logger.info("No text found: '%s'", response.url)
            item = None

        return item

    def path_from_url(self, url: str):

        subdir = url2path(url)
        outpath = os.path.join(self.outdir, subdir)

        if not os.path.exists(outpath):
            os.makedirs(outpath)

        return outpath

    def save_meta(self, data,  outpath: str):

        outpath = os.path.join(outpath, 'meta.json')
        with open(outpath, 'w', encoding='utf-8') as fobj:
            json.dump(data, fobj, ensure_ascii=False, indent=4)

    def save_snapshot(self, snapshot: str, outpath: str):

        outpath = os.path.join(outpath, 'snapshot.html')
        with open(outpath, 'w', encoding='utf-8') as fobj:
            fobj.write(snapshot)

    def filter_statuscode(self, statuscode: str):
        return statuscode != '404'

    def filter_url(self, url: str):
        ignore = url not in ignore_list
        return ignore

    def filter_mimetype(self, mimetype: str):
        return mimetype == 'text/html'


def url2path(url: str) -> str:

    url_path = urlparse(url).path

    exclude = ['http:', 'https:']
    url_list = url_path.split('/')
    url_list = list(filter(lambda s: len(s) > 0 and s not in exclude,
                           url_list))

    url_list = url_list[1:]
    path = os.path.join(*url_list)

    return path


def normalize_string(string: str) -> str:
    string = string.strip()
    string = " ".join(string.split())
    return string
