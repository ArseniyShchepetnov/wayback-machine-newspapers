"""Search engine."""
import glob
import os
from typing import Optional

from whoosh.fields import ID, TEXT, Schema
from whoosh.index import create_in
from whoosh.qparser import QueryParser

from src.search.items import JsonDocumentItem


class SearchEngineFileSystem:
    """Search query for saved pages."""

    schema = Schema(title=TEXT(stored=True),
                    content=TEXT,
                    path=ID(stored=True, unique=True))

    def __init__(self,
                 path,
                 index_dir: Optional[str] = None):

        self._path = path

        if index_dir is None:
            index_dir = os.path.join(os.path.dirname(path), '.index')

        if not os.path.exists(index_dir):
            os.mkdir(index_dir)

        self._ix = create_in(index_dir, self.schema)

    @staticmethod
    def _construct_pattern(path: str) -> str:
        return os.path.join(path, '**', '*.json')

    def analyse(self):

        writer = self._ix.writer()

        pat = self._construct_pattern(self._path)

        for doc in glob.glob(pat, recursive=True):

            item = JsonDocumentItem.from_file(doc)

            writer.add_document(title=item.title,
                                content=item.content,
                                path=item.path)

        writer.commit()

    def find_string(self, string, **kwargs):

        searcher = self._ix.searcher()
        parser = QueryParser("content", self._ix.schema)
        query = parser.parse(string)
        results = searcher.search(query, **kwargs)

        return results
