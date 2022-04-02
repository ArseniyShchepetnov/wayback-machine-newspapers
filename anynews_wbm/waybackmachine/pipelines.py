"""
Define your item pipelines here

Don't forget to add your pipeline to the ITEM_PIPELINES setting
See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
useful for handling different item types with a single interface
"""
import json
import logging
import os
import shutil
from typing import Any
from urllib.parse import urlparse

import scrapy
from itemadapter import ItemAdapter

from anynews_wbm.snapshot.db.client import DbClient, SnapshotCollectionClient
from anynews_wbm.snapshot.snapshot import Snapshot
from anynews_wbm.waybackmachine.spiders.base import SpiderWaybackMachineBase

logger = logging.getLogger(__name__)


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


def path_from_url(url: str, root_path: str) -> str:
    """Generate path from URL and makedir."""
    subdir = url2path(url)
    outpath = os.path.join(root_path, subdir)
    if not os.path.exists(outpath):
        os.makedirs(outpath)
    return outpath


class JsonWriterPipeline:
    """Write to JSON."""

    SETTING_ROOT_DIR = 'json_root_dir'
    SETTING_CLEAR = 'json_clear'

    _default_root_dir = os.path.expanduser('~/anynews_wbm')

    def __init__(self, root_dir: str, clear: bool, encoding: str = 'utf-8'):
        """
        Parameters
        ----------
        root_dir : str
            Root directory.
        """
        self.root_dir = root_dir
        self.clear = clear
        self.encoding = encoding

    def output_dir(self, spider: scrapy.Spider) -> str:
        """Returns spider output directory."""

        return os.path.join(self.root_dir, spider.name)

    @classmethod
    def from_crawler(cls,
                     crawler: scrapy.crawler.Crawler) -> 'JsonWriterPipeline':
        """Instantiate from crawler."""
        root_dir = crawler.settings.get(cls.SETTING_ROOT_DIR,
                                        cls._default_root_dir)
        clear = crawler.settings.get(cls.SETTING_CLEAR, False)

        return cls(
            root_dir=root_dir,
            clear=clear
        )

    def open_spider(self, spider: scrapy.Spider):
        """Open spider."""
        output_dir = self.output_dir(spider)

        logger.info("Output directory: %s", output_dir)

        if self.clear and os.path.exists(output_dir):
            shutil.rmtree(output_dir)

        os.makedirs(output_dir, exist_ok=True)

        filename = os.path.join(output_dir, 'name')
        with open(filename, "w", encoding=self.encoding) as fobj:
            fobj.write(spider.name)

    def process_item(self, item: Any, spider: scrapy.Spider):
        """Process item."""

        output_dir = self.output_dir(spider)

        item_dict = ItemAdapter(item).asdict()

        to_json = {
            key: val
            for key, val in item_dict.items()
            if key != 'snapshot'
        }

        outdir = path_from_url(item_dict['url'], output_dir)
        outpath = os.path.join(outdir, 'meta.json')
        with open(outpath, 'w', encoding=self.encoding) as fobj:
            json.dump(to_json, fobj, ensure_ascii=False, indent=4)

        self.save_snapshot(item_dict, outdir)

        return item

    def save_snapshot(self, snapshot: str, outpath: str):  # pylint: disable=no-self-use
        """Save snapshot to the output path."""
        outpath = os.path.join(outpath, 'snapshot.html')
        with open(outpath, 'w', encoding='utf-8') as fobj:
            fobj.write(snapshot)


class MongodbWriterPipeline:
    """Write items to mongodb."""

    CONNECTION = 'mongodb://localhost'
    DATABASE = 'anynews_wbm'

    def __init__(self):

        self.client = None
        self.db = None

    def open_spider(self, spider: SpiderWaybackMachineBase):
        """Open spider."""
        self.client = DbClient(connection=self.CONNECTION,
                               database=self.DATABASE)

        if spider.clear_database is True:
            self.client.db.drop_collection(spider.name)
            logger.info("Collection '%s' was dropped %s",
                        spider.name, spider.clear_database)

    def close_spider(self, spider: scrapy.Spider):
        """Close spider."""
        self.client.client.close()
        logger.info("Connection for spider '%s' was closed", spider.name)

    def process_item(self, item: Any, spider: scrapy.Spider):
        """Process item and save to database."""
        snapshot_db = SnapshotCollectionClient(self.client, spider.name)

        adapter_dict = ItemAdapter(item).asdict()
        data = {
            key: val
            for key, val in adapter_dict.items()
            if key != 'snapshot'
        }

        snapshot = Snapshot.from_dict(data, snapshot=adapter_dict['snapshot'])
        snapshot_db.insert(snapshot, unique=True)
