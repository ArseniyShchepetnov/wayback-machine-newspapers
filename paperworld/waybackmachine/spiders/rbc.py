"""Scraper for rbc.ru site from waybackmachine."""
import json
import logging
import os
from typing import Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup, NavigableString

from paperworld.waybackmachine.items import WaybackMachineGeneralArticleItem
from paperworld.waybackmachine.spiders.base import (SpiderWaybackMachineBase,
                                                    WaybackMachineResponseCDX)

logger = logging.getLogger(__file__)


class SpiderRBC(SpiderWaybackMachineBase):
    """rbc.ru pages parser."""

    name = "spider_rbc"

    def parse(self, response):
        """Parse response."""

        soup = BeautifulSoup(response.text)

        text = find_text(soup)

        if text is not None and len(text) > 0:

            text = normalize_string(text)

            tag_title = soup.find("div", {"class": "article__header__title"})
            title = normalize_string(tag_title.text)

            tag_date = soup.find("span", {"class": "article__header__date"})
            publish_date = tag_date.get('content', '')
            title_date = tag_date.text

            logger.info("Text found with title '%s' (date from title %s). "
                        "Text length is %d",
                        title, title_date, len(text))

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
        outpath = os.path.join(self.scraper_outdir, subdir)

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


def find_text(soup: BeautifulSoup) -> Optional[str]:

    text_list = []
    for tag in soup.find_all("div", {"class": "article__text"}):

        if not isinstance(tag, NavigableString):

            for string in soup.find_all("p"):
                text = string.text
                text_list.append(text)

    counts = {}
    for string in text_list:
        n = counts.get(string)
        if n is None:
            counts[string] = 0
        else:
            counts[string] += 1

    text_list = [key for key, val in counts.items() if val == 1]

    if len(text_list) > 0:
        text = "\n".join(text_list)
    else:
        text = None

    return text


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
