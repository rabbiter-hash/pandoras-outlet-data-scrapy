import os
import re

import scrapy
from scrapy import Selector
from ..items import PandorasoutletItem
# 入口只能以目录页进行，如果不以目录页进行，面包屑中采集不到一级目录；
"""
    思路：
    1. 入口页为二级目录页；
    2. 解析二级目录的产品，如果有翻页，就进行翻页；
    3. 定义网站、一级目录和二级目录，保存的时候需要用到。
    4. 每采集完一个目录，需要手动更改的有：
        a. start_urls
        b. first_level_category
        c. second_level_category
    
"""
"""
    # 可以优化的地方：
    # 将site，category_info，以及start_urls进行数据结构化，字典，然后从字典中去读取；
"""
class PandoraSpider(scrapy.Spider):
    name = "pandora"
    allowed_domains = ["pandoras-outlet.com"]
    start_urls = ["https://www.pandoras-outlet.com/pandora-safety-chain-outlet"]
    
    # 将网站信息定义为类变量
    site = "https://www.pandoras-outlet.com"
    category_info = {
        'first_level_category': "Safety Chain",
        'second_level_category': "safe"
    }

    def parse(self, response, **kwargs):
        # 选择器
        sel = Selector(response)
        # 产品列表
        products_lists = sel.xpath('.//div[contains(@class, "main-products")]/div[contains(@class, "product-grid-item")]')
        
        for product in products_lists:
            item = PandorasoutletItem()
            
            # 添加分类信息
            item['site'] = self.site
            item['first_level_category'] = self.category_info['first_level_category']
            item['second_level_category'] = self.category_info['second_level_category']

            product_detail_url = product.xpath('.//h4[@class="name"]/a/@href').extract_first()
            item['product_detail_url'] = product_detail_url

            yield scrapy.Request(
                url=response.urljoin(product_detail_url),
                callback=self.parse_detail_page,
                meta={'item': item}
            )
            
        # 获取下一页链接
        next_page = response.xpath('//div[contains(@class, "pagination")]//a[text()=">"]/@href').extract_first()
        # 注意提取链接的表达式
        if next_page:
            self.logger.info(f"找到下一页: {next_page}")
            yield scrapy.Request(
                url=response.urljoin(next_page),
                callback=self.parse
            )
        else:
            self.logger.info("没有下一页了，爬取结束")

    def parse_detail_page(self, response, **kwargs):
        item = response.meta['item']

        # 使用安全的数据提取方法
        selectors = {
            'product_name': './/h1[@class="heading-title"]/text()',
            'product_model': './/span[@class="p-model"]/text()',
            'product_original_price': './/li[@class="price-old"]/text()',
            'product_discount_price': './/li[@class="price-new"]/text()',
            'product_main_image': './/img[@id="image"]/@src'
        }

        for field, selector in selectors.items():
            value = response.xpath(selector).extract_first()
            if (field in ['product_original_price', 'product_discount_price']) and value:
                # 两个条件同时满足
                # print(field, value, sep="*" * 50)
                value = re.sub(r"\$", "", value)
                # print("第三次：" + value + "*"*50)
            item[field] = value or ''


        # 提取存储路径的前缀
        image_store_prefix = item['product_model']
        # model本身的前缀替换成咱们的
        replace_pattern = re.compile(r"\w+-")
        # 处理分类名称：转小写并将空格替换为下划线
        first_level = self.category_info['first_level_category'].lower().replace(' ', '_')
        second_level = self.category_info['second_level_category'].lower().replace(' ', '_')
        # 组合新的前缀
        new_prefix = f'{second_level}-'
        # 替换原有前缀
        product_model = re.sub(replace_pattern, new_prefix, item['product_model'])
        item['product_model'] = product_model

        # 使用正则表达式从主图URL中提取文件后缀
        image_suffix_match = re.search(r'\.([a-zA-Z0-9]+)(?:\?.*)?$', item['product_main_image'])
        image_suffix = image_suffix_match.group(1) if image_suffix_match else 'jpg'  # 默认使用jpg
        image_store_filename_path = f"{product_model}.{image_suffix}"
        item['image_store_url'] = 'images/{}/{}/{}/{}'.format(
            self.category_info['first_level_category'].replace(" ", "-").lower(),
            self.category_info['second_level_category'].replace(" ", "-").lower(),
            re.sub("\w+-", "", product_model),
            image_store_filename_path
        )

        # 处理详情图片
        try:
            # item['product_detail_images'] = response.xpath('.//div[@class="swiper-wrapper"]/a/@href').extract() or []
            item['product_detail_images'] = response.xpath('.//div[@class="swiper-wrapper"]/a[position() > 1]/@href').extract() or []
        except Exception as e:
            self.logger.error(f"Error extracting detail images: {str(e)}")
            item['product_detail_images'] = []

        # 处理商品描述
        try:
            item['product_description'] = response.xpath('.//div[@id="tab-description"]').extract_first() or ''
        except Exception as e:
            self.logger.error(f"Error extracting description: {str(e)}")
            item['product_description'] = ''

        yield item
