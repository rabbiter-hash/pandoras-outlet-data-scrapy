# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import re

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import scrapy
import csv
import os
from datetime import datetime
from scrapy.pipelines.files import FilesPipeline

class PandoraOutletDataToCsvPipeline:
    def __init__(self):
        # 创建保存数据的目录
        self.store_dir = 'scraped_data'
        if not os.path.exists(self.store_dir):
            os.makedirs(self.store_dir)
            
        # 定义CSV文件的表头
        self.headers = [
            'product_model',
            'product_name',
            'image_store_url',
            'product_original_price',
            'product_discount_price',
            'product_description',
            'first_level_category',
            'second_level_category',
            'product_detail_url',
            'product_main_image',
            'product_detail_images',
            'site'
        ]
        self.csv_file = None
        self.csv_writer = None

    def open_spider(self, spider):
        # 使用二级分类名称作为文件名
        """
        # 这里可以直接取在爬虫文件pandora.py中定义的变量
        # 将网站信息定义为类变量
        site = "https://www.pandoras-outlet.com"
        category_info = {
            'first_level': "Bracelets",
            'second_level': "Bangle"
        }
        """
        first_level_category = spider.category_info['first_level_category'].lower()
        second_level_category = spider.category_info['second_level_category'].lower()
        filename = f'pandoras_{first_level_category}_{second_level_category}.csv'
        filepath = os.path.join(self.store_dir, filename)
        
        # 打开CSV文件并写入表头
        self.csv_file = open(filepath, mode='w', newline='', encoding='utf-8')
        self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.headers)
        self.csv_writer.writeheader()

    def process_item(self, item, spider):
        # 创建一个新字典，只包含我们定义的表头字段
        row = {header: item.get(header, '') for header in self.headers}
        
        # 对列表类型的字段进行特殊处理
        if 'product_detail_images' in row:
            row['product_detail_images'] = '|'.join(item['product_detail_images'])
            
        # 写入数据
        self.csv_writer.writerow(row)
        return item

    def close_spider(self, spider):
        # 关闭CSV文件
        if self.csv_file:
            self.csv_file.close()

class pandoraOutletMainImageDownloadPipeline(FilesPipeline):
    def get_media_requests(self, item, info):
        # 拿到主图地址
        main_image_url = item['product_main_image']
        if main_image_url:
            yield scrapy.Request(
                url = main_image_url,
                meta={'item': item}
            )

    def file_path(self, request, response=None, info=None, *, item=None):
        # 拿到请求的item
        item = request.meta['item']
        # 图片名称以model命名
        file_prefix = item['product_model']
        file_prefix = re.sub(r"\w+-", "", item['product_model'])
        # print(file_prefix + "*"*150)
        file_suffix = item['product_main_image'].split('.')[-1]
        # print(file_suffix + "*" * 150)
        filename = file_prefix + '.' + file_suffix

        # 图片名称以 一级目录_二级目录_数字.jpg的形式保存，这个存储在item['images_store_url']中
        filename = item['image_store_url'].split('/')[-1]
        return u'{}/{}/{}/{}'.format(
            item['first_level_category'].replace(" ", "-").lower(),
                item['second_level_category'].replace(" ", "-").lower(),
                file_prefix,
                filename
        )

class pandoraOutletDetailImagesDownloadPipeline(FilesPipeline):
    def get_media_requests(self, item, info):
        for indexnum, detail_image_url in enumerate(item['product_detail_images']):
            yield scrapy.Request(
                url = detail_image_url,
                meta={'item': item, 'indexnum': indexnum}
            )

    def file_path(self, request, response=None, info=None, *, item=None):
        # 接收item
        item = request.meta['item']
        # 拿到indexnum
        indexnum = request.meta['indexnum']
        # 拿到model号
        product_model = request.meta['item']['product_model']
        product_model =re.sub(r"\w+-", "", request.meta['item']['product_model'])

        # 拿到图片后缀
        file_suffix = request.url.split(".")[-1]

        # 拼接图片名称
        filename = product_model + "_" + str(indexnum + 1) + '.' + file_suffix # xxx.jpg

        # 拿到model
        filename = item['image_store_url'].split('/')[-1].split('.')[0] + "_" + str(indexnum + 1) + '.' + file_suffix
        # 保存图片
        return u'{}/{}/{}/{}'.format(
            item['first_level_category'].replace(" ", "-").lower(),
            item['second_level_category'].replace(" ", "-").lower(),
            product_model,
            filename
        )

class PandorasoutletPipeline:
    def process_item(self, item, spider):
        return item
