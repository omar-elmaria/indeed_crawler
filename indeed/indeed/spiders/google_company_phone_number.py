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
        # Insert a new line for logging
        logging.info("\n")

        # Open the JSON files containing the company names
        with open(file=f"{output_file_name_of_indeed_crawler}.json", mode="r", encoding="utf-8") as f:
            df_crawler = json.load(f)
            df_crawler = pd.DataFrame(df_crawler)
            f.close()
        
        # Open the master JSON file containing the company phone numbers that were crawled before. This is where we will get the companies that we should NOT crawl again
        with open(file=f"output_phone_numbers_master.json", mode="r", encoding="utf-8") as f:
            df_phone_master = json.load(f)
            df_phone_master = pd.DataFrame(df_phone_master)
            f.close()

        # Pull the distinct combinations of company names and Indeed domain
        df_company_domain = df_crawler[["company_name", "job_page_url"]].drop_duplicates()
        # Pull the domain from the job page URL
        df_company_domain["job_page_url"] = df_company_domain["job_page_url"].apply(lambda x: re.findall(pattern="(?<=https:\/\/).*(?=\.indeed)", string=x)[0])
        # Rename the job_page_url column to domain
        df_company_domain = df_company_domain.rename(columns={"job_page_url": "domain"})
        # Drop duplicates again so you have unique combinations of company names and Indeed domain
        df_company_domain = df_company_domain.drop_duplicates()
        
        # Pull the distinct company names from the data frame and convert them to a list
        df_company_names = df_crawler["company_name"].unique().tolist()

        # Pull the distinct company names from the JSON file containing the phone numbers that were crawled before
        df_company_names_master = df_phone_master["company_name"].unique().tolist()

        # Create a list of the companies that will be crawled. This prevents duplication and optimizes cost
        final_company_list = []
        for i in df_company_names: # The list that was crawled today
            if i not in df_company_names_master: # The list that was crawled before
                final_company_list.append(i)
        
        # Print a message showing the companies that will be crawled
        logging.info(f"The final list of companies that will be crawled is: {final_company_list}")

        for i in final_company_list:
            # Using the Indeed domain belonging to the company name, create a search query for Google
            domain = df_company_domain[df_company_domain["company_name"] == i]["domain"].values[0]
            if domain == "de":
                search_query_suffix = "Telefonnummer+in+Deutschland"
            elif domain == "ca":
                search_query_suffix = "phone+number+in+Toronto%2C+Canada"
            
            # Create the search query
            search_query = "https://www.google.com/search?hl=en&lr=lang_en&q=" + i.replace(" ", "+") + "+" + search_query_suffix
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

        output_dict = {
            "company_name": response.meta["company_name"],
            "search_query": response.meta["search_query"],
            "phone_number": phone_number
        }

        yield output_dict

        # First, open the master JSON file containing the phone numbers to load the data and extend it by "output_dict"
        with open(file="output_phone_numbers_master.json", mode="r", encoding="utf-8") as f:
            new_phone_numbers = json.load(f)
            new_phone_numbers.extend([output_dict])
            f.close()

        # Append "new_phone_numbers" to the newly crawled phone numbers to "output_phone_numbers_master.json"
        with open(file="output_phone_numbers_master.json", mode="w", encoding="utf-8") as f:
            json.dump(obj=new_phone_numbers, fp=f, ensure_ascii=False, indent=0)
            f.close()


# Run the spider
full_settings_dict = custom_settings_zyte_api_dict.copy()
full_settings_dict.update({
    "FEEDS": {f"{output_file_name_of_google_crawler}.json":{"format": "json", "overwrite": True, "encoding": "utf-8"}},
    "LOG_FILE": f"{output_name_of_indeed_logs_file}.log"
})
process = CrawlerProcess(settings=full_settings_dict)
process.crawl(GoogleSpider)
process.start()