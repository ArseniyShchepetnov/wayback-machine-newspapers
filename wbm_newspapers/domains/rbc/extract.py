"""Data extraction from RBC articles."""
import re
from datetime import datetime
from typing import List, Optional

from wbm_newspapers.extaction.extraction import BaseExtractor
from wbm_newspapers.extaction.transforms import (BaseSnapshotTransfrom,
                                                 RemoveTagsByName,
                                                 SnapshotTransformPipeline)
from wbm_newspapers.extaction.utils import text_tags_class_pattern


class RbcExtractor(BaseExtractor):
    """Extractor from rbc.ru newspaper."""

    @staticmethod
    def preprocess_pipeline() -> BaseSnapshotTransfrom:
        """Returns default preprocess pipeline."""
        return SnapshotTransformPipeline([
            RemoveTagsByName(['script', 'img', 'svg', 'style', 'button'])
        ])

    def get_text(self) -> str:
        text = text_tags_class_pattern(self.soup,
                                       "article__text.*",
                                       "div")
        return text

    def get_title(self) -> str:
        return text_tags_class_pattern(self.soup,
                                       "article__header__title",
                                       "div")

    def get_authors(self) -> List[str]:
        return []

    def get_datetime(self) -> Optional[datetime]:
        return get_url_date_iso(self.url)

    def get_header_datetime(self) -> str:
        return text_tags_class_pattern(self.soup,
                                       "article__header__date",
                                       "span")


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
