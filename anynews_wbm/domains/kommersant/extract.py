"""Data extraction from RBC articles."""
import re
from datetime import datetime
from typing import List, Optional

from anynews_wbm.extaction.extraction import BaseExtractor
from anynews_wbm.extaction.utils import text_tags_class_pattern


class KommersantExtractor(BaseExtractor):

    def get_text(self) -> str:
        text = text_tags_class_pattern(self.soup,
                                       "doc__text",
                                       "p")
        return text

    def get_title(self) -> str:
        return text_tags_class_pattern(self.soup,
                                       "doc_header__name",
                                       "h1")

    def get_authors(self) -> List[str]:
        return []

    def get_datetime(self) -> Optional[datetime]:
        return get_url_date_iso(self.url)

    def get_header_datetime(self) -> str:
        return text_tags_class_pattern(self.soup,
                                       "doc_header__time",
                                       "div")


def get_url_date_iso(url: str) -> Optional[datetime]:
    """Try to get ISO date from URL."""
    result = None
    for pat, date in [(r"/\d{4}/\d{2}/\d{2}/", r'/%Y/%m/%d/'),
                      (r"/\d{2}/\d{2}/\d{4}/", r'/%d/%m/%Y/')]:
        match = re.search(pat, url)
        if match is not None:
            data = match.group()
            result = datetime.strptime(data, date)
            break
    return result
