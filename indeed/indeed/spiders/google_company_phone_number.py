import scrapy
import json
import pandas as pd
import re
from inputs import (
    custom_settings_zyte_api_dict,
    output_file_name_of_indeed_crawler,
    output_file_name_of_google_crawler,
    output_name_of_indeed_logs_file
)
from scrapy.crawler import CrawlerProcess
import logging


class GoogleSpider(scrapy.Spider):
    name = 'google_spider'
    
    def start_requests(self):
        # Open the JSON files containing the company names
        with open(file=f"{output_file_name_of_indeed_crawler}.json", mode="r", encoding="utf-8") as f:
            df_crawler = json.load(f)
            df_crawler = pd.DataFrame(df_crawler)
            f.close()

        # Pull the distinct company names from the data frame and convert them to a list
        df_company_names = df_crawler["company_name"].unique().tolist()

        for i in df_company_names:
            search_query = "https://www.google.com/search?hl=en&lr=lang_en&q=" + i.replace(" ", "+") + "+" + "phone+number+in+Toronto%2C+Canada"
            logging.info(f"Send a request to Google with the following search query --> {search_query}")
            yield scrapy.Request(
                url=search_query,
                callback=self.parse,
                meta={"company_name": i, "search_query": search_query}
            )

    def parse(self, response):
        # The first choice of a selector for crawling the phone number
        phone_number_1 = response.xpath("//span[contains(@aria-label, 'phone') or contains(@aria-label, 'Phone')]/text()").get()
        
        # Sometimes, the response yields a different HTML code. In this case, we use another selector. However, this crawled text has to be cleaned
        phone_number_2 = response.xpath("//div[contains(text(), '+1')]/text()").get()
        if phone_number_2 is not None:
            phone_number_2 = re.findall(pattern="\+(?<=\+)[0-9\s\-]+", string=phone_number_2)[0]

        # Pick one phone number out of the two
        if phone_number_1 is not None:
            # If phone_number_1 (main selection) is not None, use it
            phone_number = phone_number_1
        else:
            # If phone_number_1 (main selection) is None, check if phone_number_2 is not None. If it is indeed not None, use it. If it is None, set phone_number to None
            if phone_number_2 is not None:
                phone_number = phone_number_2
            else:
                phone_number = None

        yield {
            "company_name": response.meta["company_name"],
            "search_query": response.meta["search_query"],
            "phone_number": phone_number
        }

# Run the spider
full_settings_dict = custom_settings_zyte_api_dict.copy()
full_settings_dict.update({
    "FEEDS": {f"{output_file_name_of_google_crawler}.json":{"format": "json", "overwrite": True, "encoding": "utf-8"}},
    "LOG_FILE": f"{output_name_of_indeed_logs_file}.log"
})
process = CrawlerProcess(settings=full_settings_dict)
process.crawl(GoogleSpider)
process.start()