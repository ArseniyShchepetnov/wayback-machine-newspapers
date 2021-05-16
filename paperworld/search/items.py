"""Document items in file system for engine."""
import abc
import json
from typing import Dict, Any


class FileSystemDocumentItem(metaclass=abc.ABCMeta):
    """Abstract file system document item for search engine."""

    @abc.abstractclassmethod
    def from_file(cls, path: str) -> 'FileSystemDocumentItem':
        """Read item from file."""

    @abc.abstractproperty
    def title(self) -> str:
        """Returns title for engine."""

    @abc.abstractproperty
    def content(self) -> str:
        """Returns content for engine."""

    @abc.abstractproperty
    def path(self) -> str:
        """Returns path for engine."""


class JsonDocumentItem(FileSystemDocumentItem):
    """JSON file system document item."""

    def __init__(self, data: Dict[str, Any], path: str):
        """
        Parameters
        ----------
        data : Dict[str, Any]
            Dict with data.
        path : str
            Path string.
        """

        self._data = data
        self._path = path

    @property
    def data(self):
        return self._data

    @classmethod
    def from_file(cls, path: str) -> 'FileSystemDocumentItem':
        """Read item from file."""

        with open(path, 'r') as json_file:
            data = json.load(json_file)

        return cls(data, path)

    @property
    def title(self) -> str:
        """Returns title for engine."""
        return self._data['title']

    @property
    def content(self) -> str:
        """Returns content for engine."""
        return self._data['text']

    @property
    def path(self) -> str:
        """Returns path for engine."""
        return self._path
