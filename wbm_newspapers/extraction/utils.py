"""Utility functions."""
import re
import urllib
from typing import List, Optional, Union

import pandas as pd
from bs4 import BeautifulSoup


def normalize_string(string: str) -> str:
    """
    Normalize string.

    Strip whitespaces and remove newlines.
    """
    string = string.strip()
    string = " ".join(string.split())
    return string


def get_url_path_section(url: str, n_section: int = 0) -> str:
    """Get first path from url."""
    path = urllib.parse.urlparse(url).path  # type: ignore
    return path.split('/')[n_section + 1]


def path_stat(urls: pd.Series) -> pd.Series:
    """First sections counts."""
    sections = urls.apply(get_url_path_section)
    return sections.value_counts()


def text_tags_class_pattern(soup: BeautifulSoup,
                            class_pattern: str,
                            tag_name: Union[str, List[str]]) \
        -> str:
    """
    Helper function to extract text from tags
    with classes fullmatch pattern.
    """
    expr = re.compile(class_pattern)

    find_all = soup.find_all(tag_name,
                             class_=lambda x: x and expr.fullmatch(x))

    tag_text = [tag.get_text(" ") for tag in find_all]
    text = "\n".join(tag_text)
    return normalize_string(text)


def func_check(class_: Optional[str],
               expr: re.Pattern,
               expr_exclude: re.Pattern):
    """Check expression."""
    return (class_
            and expr.fullmatch(class_)
            and not expr_exclude.fullmatch(class_))
