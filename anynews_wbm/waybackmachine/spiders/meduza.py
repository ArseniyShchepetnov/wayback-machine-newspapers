"""Meduza site scraping."""
import itertools
import json
import logging
import os
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from waybackmachine_cdx import WaybackMachineCDX
from anynews_wbm.waybackmachine.items import WaybackMachineGeneralArticleItem
from anynews_wbm.waybackmachine.spiders.base import (SpiderWaybackMachineBase,
                                                     WaybackMachineResponseCDX)

logger = logging.getLogger(__file__)


class SpiderMeduza(SpiderWaybackMachineBase):

    name = "spider_meduza"

    def parse(self, response):
        """Parse response."""

        soup = BeautifulSoup(response.text)

        tag_text = soup.find("div", {"class": "GeneralMaterial-article"})

        if tag_text is not None:

            text = normalize_string(tag_text.text)

            # tag_title = soup.find("div", {"class": "article__header__title"})
            title = ''  # normalize_string(tag_title.text)

            # soup.find("span", {"class": "article__header__date"})

            publish_date = ''  # tag_date.get('content', '')
            title_date = ''  # tag_date.text

            url_pars = WaybackMachineResponseCDX.from_archive_url(response.url)

            item = WaybackMachineGeneralArticleItem(
                text=text,
                title=title,
                publish_date=publish_date,
                title_date=title_date,
                url=response.url,
                timestamp=url_pars['timestamp'],
                original=url_pars['original'],
                snapshot=response.text
            )

        else:
            logger.info("No text found: '%s'", response.url)
            item = None

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


def normalize_string(string: str) -> str:
    string = string.strip()
    string = " ".join(string.split())
    return string
