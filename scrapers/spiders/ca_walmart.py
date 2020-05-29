import json

import scrapy
from scrapy import Request

from scrapers.items import ProductItem


class CaWalmartSpider(scrapy.Spider):
    name = "ca_walmart"
    allowed_domains = ["walmart.ca"]
    start_urls = ["https://www.walmart.ca/en/grocery/fruits-vegetables/fruits/N-3852"]
    base_walmart_url = 'https://www.walmart.ca'
    base_branch_url = '/api/product-page/find-in-store?latitude=48.4120872&longitude=-89.2413988&lang=en&upc='

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

        sku = detail['product']['activeSkuId']
        first_upc = detail['entities']['skus'][sku]['upc'][0]
        barcodes = ' '.join(detail['entities']['skus'][sku]['upc'])
        image_url = detail['entities']['skus'][sku]['images'][0]['large']['url']

        product_item = {
            'store': 'Walmart',
            'barcodes': barcodes,
            'sku': sku,
            'brand': detail['entities']['skus'][sku]['brand']['name'],
            'name': detail['entities']['skus'][sku]['name'],
            'description': detail['entities']['skus'][sku]['longDescription'],
            'package': detail['product']['item']['description'],
            'image_url': image_url
        }

        url_branch = '{}{}{}'.format(
            self.base_walmart_url,
            self.base_branch_url,
            first_upc
        )

        yield Request(url_branch, callback=self.branch_product, cb_kwargs={'product_item': product_item})

    def branch_product(self, response, product_item):
        json_response = json.loads(response.text)
        for branch in json_response['info']:
            product_instance = ProductItem(**product_item)
            product_instance['branch'] = branch['id']
            product_instance['stock'] = branch['availableToSellQty']
            product_instance['price'] = branch.get('sellPrice', 0)

            yield product_instance  # item
