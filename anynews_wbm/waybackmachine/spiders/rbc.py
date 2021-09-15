"""Scraper for rbc.ru site from waybackmachine."""
import logging
from typing import Optional

from bs4 import BeautifulSoup, NavigableString

from anynews_wbm.waybackmachine.items import WaybackMachineGeneralArticleItem
from anynews_wbm.waybackmachine.spiders.base import (SpiderWaybackMachineBase,
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


def normalize_string(string: str) -> str:
    string = string.strip()
    string = " ".join(string.split())
    return string
