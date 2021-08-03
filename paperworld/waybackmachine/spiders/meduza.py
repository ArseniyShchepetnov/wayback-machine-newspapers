"""Meduza site scraping."""
import itertools
import json
import logging
import os
import re
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from paperworld.cdx import WaybackMachineCDX
from paperworld.utils.timestamp import timestamp_month_ru2en
from paperworld.waybackmachine.items import WaybackMachineGeneralArticleItem
from paperworld.waybackmachine.spiders.base import (SpiderWaybackMachineBase,
                                                    WaybackMachineResponseCDX)
from paperworld.waybackmachine.spiders.utils import check_tag_attr_re

logger = logging.getLogger(__file__)


class SpiderMeduza(SpiderWaybackMachineBase):

    name = "spider_meduza"

    _rm_pat = re.compile("^(?:DonatesTeaser|RelatedBlock).*")
    _pat_class_2 = re.compile("^style__Material.*")
    _pat_class_par_2 = re.compile("^style__Paragraph.*")

    def _article_remove_filter(self, tag):
        result = False

        if tag.name == 'div' and tag.has_attr('class'):
            for cur in tag.attrs['class']:
                if self._rm_pat.match(cur):
                    result = True
                    break

        return result

    def _get_article_timestamp(self, tag):

        timestamp_tags = tag.find_all('time')

        if len(timestamp_tags) > 1:
            logger.warning("Multiple timestamp tags detected.")

        timestamp = timestamp_tags[0].text

        return timestamp

    def _parse_1(self, soup: BeautifulSoup, url: str):

        article = soup.html.body.find('div',
                                      {'class': "GeneralMaterial-article"})

        title = soup.html.head.title.text

        publish_date = self._get_article_timestamp(soup.html.body)

        tag_banner_ino = article.find_all('div', {'id': 'div-gpt-ad'})
        for tag in tag_banner_ino:
            tag.decompose()

        tag_other = article.find_all(self._article_remove_filter)
        for tag in tag_other:
            tag.decompose()

        text = article.get_text("\n")
        text = normalize_string(text)

        outpath = self.path_from_url(url)

        url_pars = WaybackMachineResponseCDX.from_archive_url(url)

        item = WaybackMachineGeneralArticleItem(
            text=text,
            title=title,
            publish_date=publish_date,
            title_date='',
            url=url,
            timestamp=url_pars['timestamp'],
            original=url_pars['original'],
            path=outpath
        )

        return item, outpath

    def _parse_2(self, soup: BeautifulSoup, url: str):

        article = soup.html.body.find(
            lambda x: check_tag_attr_re(x, self._pat_class_2, 'class'))

        par_tags = soup.find_all(
            lambda tag: check_tag_attr_re(tag, self._pat_class_par_2, 'class')
        )

        text = [normalize_string(par.get_text()) for par in par_tags]
        text = "\n".join(text)

        title = soup.html.head.title.text

        publish_date = self._get_article_timestamp(soup.html.body)

        tag_banner_ino = article.find_all('div', {'id': 'div-gpt-ad'})
        tag_banner_ino.decompose()

        tag_other = article.find_all(self._article_remove_filter)
        for tag in tag_other:
            tag.decompose()

        outpath = self.path_from_url(url)

        url_pars = WaybackMachineResponseCDX.from_archive_url(url)

        item = WaybackMachineGeneralArticleItem(
            text=text,
            title=title,
            publish_date=publish_date,
            title_date='',
            url=url,
            timestamp=url_pars['timestamp'],
            original=url_pars['original'],
            path=outpath
        )

        return item, outpath

    def parse(self, response):
        """Parse response."""

        soup = BeautifulSoup(response.text)

        case_1 = soup.html.body.find(
            'div', {'class': "GeneralMaterial-article"}
        ) is not None

        case_2 = soup.html.body.find(
            lambda tag: check_tag_attr_re(tag, self._pat_class_2, 'class')
        ) is not None

        if case_1:

            item, outpath = self._parse_1(soup, response.url)

            self.save_snapshot(response.text, outpath)

            logger.info("FOUND TEXT: '%s'", outpath)

        elif case_2:

            item, outpath = self._parse_2(soup, response.url)

            self.save_snapshot(response.text, outpath)

            logger.info("FOUND TEXT: '%s'", outpath)

        else:
            logger.info("NO TEXT FOUND: '%s'", response.url)
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
