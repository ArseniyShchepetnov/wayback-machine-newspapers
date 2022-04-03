"""Content extractor."""
import abc
import datetime
from typing import List, Optional

from bs4 import BeautifulSoup

from wbm_newspapers.extaction.transforms import (BaseSnapshotTransfrom,
                                                 RemoveSpanNotDropcap,
                                                 RemoveTagsByName,
                                                 SnapshotTransformPipeline)
from wbm_newspapers.extaction.utils import normalize_string


class BaseExtractor(metaclass=abc.ABCMeta):
    """Basic snapshot extraction."""

    def __init__(self, soup: BeautifulSoup, url: str):
        preprocess = self.preprocess_pipeline()
        self._soup = preprocess(soup)
        self._url = url

    @property
    def url(self) -> str:
        """Get url."""
        return self._url

    @property
    def soup(self) -> BeautifulSoup:
        """Return beautiful soup object."""
        return self._soup

    def text(self) -> str:
        """Get all the text."""
        return normalize_string(self.soup.get_text(" "))

    @staticmethod
    def preprocess_pipeline() -> BaseSnapshotTransfrom:
        """Returns default preprocess pipeline."""
        return SnapshotTransformPipeline([
            RemoveTagsByName(['script', 'img', 'svg', 'style', 'button']),
            RemoveSpanNotDropcap()
        ])

    @abc.abstractmethod
    def get_text(self) -> str:
        """Get article text."""

    @abc.abstractmethod
    def get_title(self) -> str:
        """Get article title."""

    @abc.abstractmethod
    def get_authors(self) -> List[str]:
        """List of authors."""

    @abc.abstractmethod
    def get_datetime(self) -> Optional[datetime.datetime]:
        """Article datetime."""

    @abc.abstractmethod
    def get_header_datetime(self) -> str:
        """Get datetime from header."""
