# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class PandorasoutletItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    site = scrapy.Field()
    first_level_category = scrapy.Field()
    second_level_category = scrapy.Field()
    product_name = scrapy.Field()
    product_original_price = scrapy.Field()
    product_discount_price = scrapy.Field()
    product_model = scrapy.Field()
    product_size = scrapy.Field()
    product_description = scrapy.Field()
    product_main_image = scrapy.Field()
    product_detail_images = scrapy.Field()
    product_detail_url = scrapy.Field()
    image_store_url = scrapy.Field()
