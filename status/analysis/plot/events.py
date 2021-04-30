"""Visualize events"""
import json
import pathlib
from collections.abc import Iterator


class LocalDataIterator(Iterator):

    def __init__(self, data_dir: str):

        path = pathlib.Path(data_dir)
        self.glob = path.glob('**/meta.json')

    def __iter__(self):
        return self

    def __next__(self):

        item = next(self.glob)

        return item


class ParseItem:

    def filter_header(self, path: str, word: str):

        with open(path) as json_file:
            data = json.load(json_file)
