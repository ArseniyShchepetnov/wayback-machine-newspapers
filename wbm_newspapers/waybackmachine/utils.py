"""Utilities for waybackmachine."""
import os
from urllib.parse import urlparse


def url2path(url: str) -> str:
    """Convert URL to the path."""
    url_path = urlparse(url).path
    exclude = ['http:', 'https:']
    url_list = url_path.split('/')
    url_list = list(filter(lambda s: len(s) > 0 and s not in exclude,
                           url_list))
    url_list = url_list[1:]
    path = os.path.join(*url_list)
    return path
