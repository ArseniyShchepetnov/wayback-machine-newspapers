# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import os
import json


class JsonWriterPipeline:

    def process_item(self, item, spider):

        item_dict = ItemAdapter(item).asdict()

        outpath = os.path.join(item_dict['path'], 'meta.json')
        with open(outpath, 'w', encoding='utf-8') as fobj:
            json.dump(item_dict, fobj, ensure_ascii=False, indent=4)

        return item
