"""
Define your item pipelines here

Don't forget to add your pipeline to the ITEM_PIPELINES setting
See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
useful for handling different item types with a single interface
"""
import logging
import os
import shutil
from typing import Any

import scrapy
from itemadapter import ItemAdapter
from wbm_snapshot.db.client import DbClient, SnapshotCollectionClient
from wbm_snapshot.snapshot import Snapshot

from wbm_newspapers.waybackmachine.spiders.base import SpiderWaybackMachineBase
from wbm_newspapers.waybackmachine.utils import url2path

logger = logging.getLogger(__name__)


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

        adapter_dict = ItemAdapter(item).asdict()
        data = {
            key: val
            for key, val in adapter_dict.items()
            if key != 'snapshot'
        }

        snapshot = Snapshot.from_dict(data, snapshot=adapter_dict['snapshot'])

        outdir = path_from_url(data['url'], output_dir)
        snapshot.save(outdir)


class MongodbWriterPipeline:
    """Write items to mongodb."""

    CONNECTION = 'mongodb://localhost'
    DATABASE = 'anynews_wbm'

    def __init__(self):
        self.client = None

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
