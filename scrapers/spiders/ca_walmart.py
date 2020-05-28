import json

import scrapy
from scrapy import Request

from scrapers.items import ProductItem


class CaWalmartSpider(scrapy.Spider):
    name = "ca_walmart"
    allowed_domains = ["walmart.ca"]
    start_urls = ["https://www.walmart.ca/en/grocery/fruits-vegetables/fruits/N-3852"]
    base_walmart_url = 'https://www.walmart.ca'

    def parse(self, response):
        products = response.css('a.product-link::attr("href")').getall()

        for product in products:
            url_product = '{0}{1}'.format(self.base_walmart_url, product)
            yield Request(url=url_product, callback=self.product_detail)

        next_page = response.css('a.page-select-list-btn::attr("href")').get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def product_detail(self, response):
        all_js = response.css('script::text').getall()
        product_specs = [js for js in all_js if 'upc' in js][0]
        json_product = product_specs.replace('window.__PRELOADED_STATE__=', '')[:-1]
        detail = json.loads(json_product)
        print(detail['product']['item']['id'])
        ProductItem()
