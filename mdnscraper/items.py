# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class MdnPageItem(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    section = scrapy.Field()
    breadcrumb = scrapy.Field()
    content = scrapy.Field()
    headings = scrapy.Field()
    scraped_at = scrapy.Field()
    pass
