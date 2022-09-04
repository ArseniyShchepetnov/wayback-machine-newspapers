"""
Define here the models for your scraped items

See documentation in:
https://docs.scrapy.org/en/latest/topics/items.html
"""
import scrapy


class WaybackMachineGeneralArticleItem(scrapy.Item):
    """Parsed item from article."""

    text = scrapy.Field()
    title = scrapy.Field()
    summary = scrapy.Field()
    publish_date = scrapy.Field()
    title_date = scrapy.Field()
    url_date = scrapy.Field()
    url = scrapy.Field()
    path = scrapy.Field()
    timestamp = scrapy.Field()
    original = scrapy.Field()
    snapshot = scrapy.Field()
