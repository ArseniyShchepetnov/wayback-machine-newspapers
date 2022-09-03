"""Snapshot transformations."""
import abc
from collections.abc import Iterable
from typing import List, Optional

from bs4 import BeautifulSoup


class BaseSnapshotTransform(metaclass=abc.ABCMeta):  # pylint: disable=too-few-public-methods
    """Transform BeautifulSoup object."""

    def __call__(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Transform"""


class SnapshotTransformPipeline(BaseSnapshotTransform):  # pylint: disable=too-few-public-methods
    """Transformations pipeline."""

    def __init__(self, transforms: Iterable):
        """
        Parameters
        ----------
        transforms : Iterable
            List of transformations.
        """
        self._transforms = transforms

    def __call__(self, soup: BeautifulSoup) -> BeautifulSoup:
        for func in self._transforms:
            soup = func(soup)
        return soup


class RemoveTagsByName(BaseSnapshotTransform):  # pylint: disable=too-few-public-methods
    """Remove tags with specified names."""

    def __init__(self, names: Optional[List[str]] = None):
        """
        Parameters
        ----------
        names : Optional[List[str]], optional
            Names, by default None.
            If None names are ['script', 'img', 'svg', 'style'].
        """
        if names is None:
            names = ['script', 'img', 'svg', 'style']
        self._names = names

    def __call__(self, soup: BeautifulSoup) -> BeautifulSoup:
        for tag in soup.find_all(name=self._names):
            tag.extract()
        return soup


class RemoveSpanNotDropcap(BaseSnapshotTransform):  # pylint: disable=too-few-public-methods
    """Remove span tags if their text length is not 1."""

    def __call__(self, soup: BeautifulSoup) -> BeautifulSoup:

        for tag in soup.find_all(name="span"):
            if len(tag.text.strip()) != 1:
                tag.extract()

        return soup
