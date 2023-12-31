"""
Project: Web scraping for customer reviews
Author: Hào Cui
Date: 07/04/2023
"""
import json
import re
from urllib.parse import urlparse, parse_qs

import scrapy
from scrapy import Request

from webscrapy.items import WebscrapyItem


class SpiderSpider(scrapy.Spider):
    name = "spider"
    allowed_domains = ["www.gotools.de", "api.bazaarvoice.com"]
    headers = {}  

    def start_requests(self):
        # keywords = ['Stanley', 'Black+Decker', 'Craftsman', 'Porter-Cable', 'Bostitch', 'MAC Tools', 'Lista', 'Irwin', 'Lenox', 'CribMaster', 'Powers Fasteners', 'cub-cadet', 'hustler', 'troy-bilt', 'BigDog Mower',]
        exist_keywords = ['dewalt', 'stanley'] # black-decker is too less
        
        # company = 'Stanley Black and Decker'
        # from search words to generate product_urls
        for keyword in exist_keywords:
            push_key = {'keyword': keyword}
            search_url = f'https://www.gotools.de/marken/{keyword}'

            yield Request(
                url=search_url,
                callback=self.parse,
                cb_kwargs=push_key,
            )

    def parse(self, response, **kwargs):
        # Extract the pages of product_urls
        last_link = response.xpath('//*[@id="page-body"]//nav[@class="pagination-container"]/ul//li[@class="item pag-arrow-right"]/a[@aria-label="Zur letzten Seite"]/@href')[0].extract()
        
        # Extract the page number from the last link
        parsed_url = urlparse(last_link)
        query_params = parse_qs(parsed_url.query)
        page_number = int(query_params.get('page')[0])

        # Based on pages to build product_urls
        keyword = kwargs['keyword']
        product_urls = [f'https://www.gotools.de/search?query={keyword}&page={page}' for page
                        in range(1, page_number + 1)]  # page_number + 1

        for product_url in product_urls:
            yield Request(url=product_url, callback=self.product_parse, meta={'product_brand': keyword})

    def product_parse(self, response: Request, **kwargs):
        product_brand = response.meta['product_brand']
        product_list = response.xpath('//*[@id="page-body"]//ul[@class="product-list fx-row grid cross-box"]/li')

        for product in product_list:
            product_id = re.search(r'{"item":{"id":(\d+)', product.extract()).group(1)
            product_name = re.search(r'"name1":"(.*?)",', product.extract()).group(1)
            product_model = re.search(r'"number":"(.*?)",', product.extract()).group(1)
            product_brand = re.search(r'"externalName":"(.*?)"', product.extract()).group(1)
            customer_review_url = f'https://www.gotools.de/rest/feedbacks/feedback/helper/feedbacklist/{product_id}/1?feedbacksPerPage=10'

            yield Request(url=customer_review_url, callback=self.review_parse, meta={'product_id': product_id, 'product_name': product_name, 'product_brand':product_brand, 'product_model':product_model})

    def review_parse(self, response: Request, **kwargs):
        product_id = response.meta['product_id']
        product_name = response.meta['product_name']
        product_brand = response.meta['product_brand']
        product_model = response.meta['product_model']
        datas = json.loads(response.body)
        batch_results = datas.get('feedbacks', {})

        for i in range(len(batch_results)):
            item = WebscrapyItem()
            try:
                item['review_id'] = batch_results[i].get('feedbackComment', 'N/A').get('commentId', 'N/A')
                item['product_name'] = product_name or product_id
                item['product_website'] = 'gotools_de'
                item['product_type'] = 'N/A'
                item['product_brand'] = product_brand
                item['product_model'] = product_model
                # item['customer_name'] = batch_results[i].get('authorName', 'Anonymous')
                item['customer_name'] = batch_results[i].get('authorName') if batch_results[i].get('authorName') else 'Anonymous'
                item['customer_rating'] = batch_results[i].get('feedbackRating', 'N/A').get('rating', 'N/A').get('ratingValue', 'N/A')
                item['customer_date'] = batch_results[i].get('feedbackComment', 'N/A').get('comment', 'N/A').get('createdAt', 'N/A')
                item['customer_review'] = batch_results[i].get('feedbackComment', 'N/A').get('comment', 'N/A').get('message', 'N/A')
                item['customer_support'] = batch_results[i].get('TotalPositiveFeedbackCount', 'N/A')
                item['customer_disagree'] = batch_results[i].get('TotalNegativeFeedbackCount', 'N/A')

                yield item
            except Exception as e:
                break


