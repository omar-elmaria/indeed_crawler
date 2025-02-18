import scrapy
from inputs import (
    custom_settings_zyte_api_dict,
    num_listings_per_page,
    page_index_step,
    page_index_max,
    output_file_name_of_indeed_crawler,
    output_name_of_indeed_logs_file
)
import re
from math import ceil
import logging
from datetime import datetime
from scrapy.crawler import CrawlerProcess
from urllib.parse import urljoin

class IndeedZyteAPISpider(scrapy.Spider):
    name = 'indeed_zyte_api'
    
    def start_requests(self):
        # Insert a new line for logging
        logging.info("\n")

        urls = [
            # Canada
            # "https://ca.indeed.com/jobs?l=Greater+Toronto+Area%2C+ON&sc=0kf%3Aocc%286YCJB%29%3B&radius=35&sort=date&vjk=f55ce01235a88065", # URL 1
            # "https://ca.indeed.com/jobs?q=Human&l=Greater+Toronto+Area%2C+ON&radius=100&sort=date&vjk=5bd4496580222855", # URL 2

            # Germany
            "https://de.indeed.com/jobs?q=Circular%20Economy&l=Deutschland&filter=0", # URL 1
            "https://de.indeed.com/jobs?q=Circularity&l=Deutschland&filter=0&vjk=17f1151bb19093cb", # URL 2
            "https://de.indeed.com/jobs?q=Kreislaufwirtschaft&l=Deutschland&filter=0&vjk=5811fd5a06ed88c4" # URL 3
        ]

        for idx, i in enumerate(urls):
            yield scrapy.Request(
                url=i,
                callback=self.parse,
                meta={
                    "crawler_name": f"crawler_{idx + 1}",
                    "base_url": i,
                    "zyte_api_automap": {
                        "browserHtml": True,
                        "javascript": True,
                    }
                }
            )

    def parse(self, response):
        # Extract the total number of jobs as a string
        num_jobs = response.xpath("//div[contains(@class, 'jobsearch-JobCountAndSortPane-jobCount')]/span/text()").get()
        logging.info(f"The total number of jobs under the URL of {response.meta['crawler_name']}: {num_jobs}")

        # Extract the number of jobs as an integer
        num_jobs = int(''.join(re.findall(pattern=r"\d+", string=num_jobs)))

        # Calculate the index corresponding to the number of pages we will loop over
        num_page_loop_all = ceil(num_jobs / num_listings_per_page)
        page_index_all = (num_page_loop_all - 1) * page_index_step # 15 is the number of listings per page. The index = (number of pages - 1) x 10. For example, 14 pages means that the index would end at (14 - 1) x 10 = 130
        
        # The maximum number of pages shown by indeed is 55 pages. This corresponds to index 540. Take the min of page_index_all + page_index_step (the step = 10) or 540 as the for loop's range end
        if page_index_all <= page_index_max:
            for_loop_end_range = page_index_all
        else:
            for_loop_end_range = page_index_max
        
        # Calculate the number of pages we will actually loop over
        num_page_loop_actual = for_loop_end_range / page_index_step + 1
        
        # Print a message showing the number of pages we are supposed to loop over, the for loop's end range index, and the number of pages we will actually loop over
        logging.info(f"The number of pages we are supposed to loop over under the URL of {response.meta['crawler_name']} is: {ceil(num_jobs / num_listings_per_page)}. The for_loop_end_range index is: {for_loop_end_range}, which makes the number of pages we will actually loop over: {num_page_loop_actual}")

        # Loop over every page until all job listings are crawled
        page_counter = 1
        for i in range(0, for_loop_end_range + page_index_step, page_index_step):
            logging.info(f"Crawling page number {page_counter} with index {i} from the URL of {response.meta['crawler_name']}")
            listing_page_url = response.meta["base_url"] + f"&start={i}"
            yield scrapy.Request(
                url=listing_page_url,
                callback=self.parse_listing_page,
                meta={
                    "crawled_page_rank": page_counter,
                    "listing_page_url": listing_page_url,
                    "crawler_name": response.meta["crawler_name"],
                    "zyte_api_automap": {
                        "browserHtml": True,
                        "javascript": True,
                    }
                },
                dont_filter=True
            )
            page_counter += 1

    def parse_listing_page(self, response):
        # Number of Listings
        # Old listings selector (18-08-2023): //ul[@class='jobsearch-ResultsList css-0']/li/div[not(contains(@id, 'mosaic'))]
        listings = response.xpath("//div[@id='mosaic-provider-jobcards']/ul/li/div[not(contains(@id, 'mosaic'))]")
        for li in listings:
            job_title_name = li.xpath(".//h2[contains(@class, 'jobTitle')]/a/text() | .//h2[contains(@class, 'jobTitle')]/a/span/text()").get()
            if job_title_name is None: # Sometimes, the the HTML content under "li" is NULL. If this is the case, don't add anything to the "output_dict"
                logging.info(f"The job_title_name of {li} under the URL of {response.meta['crawler_name']} is None. Continuing the the next listing")
                continue
            else:
                # Clean the crawled fields
                # job_indeed_url
                try:
                    job_indeed_url = urljoin(response.url, li.xpath(".//h2[contains(@class, 'jobTitle')]/a/../@href").get())
                except TypeError:
                    job_indeed_url = None

                # posted_on
                posted_on = li.xpath(".//span[@data-testid='myJobsStateDate']/text()").get()
                
                # company_name. Sometimes the company name exists with or without a URL, so we need two selectors
                company_name_with_url = li.xpath(".//span[@data-testid='company-name']/a/text()").get()
                company_name_wout_url = li.xpath(".//span[@data-testid='company-name']/text()").get()
                company_name = company_name_with_url if company_name_with_url is not None else company_name_wout_url

                # city and remote
                city = li.xpath(".//div[@data-testid='text-location']/text()").get()
                unwanted_words = [
                    # Canada
                    "Temporarily Remote in ", "Remote in ", "Hybrid remote in ",
                    
                    # Germany
                    "Zum Teil im Homeoffice in", "Homeoffice in"
                ]
                if city is not None:
                    if bool([wo for wo in unwanted_words if(wo in city)]): # If TRUE (i.e., if an unwanted sub-string exists in city, remove it from the main string, which is city) 
                        # Set the remote variable to the value of the unwanted word
                        remote = re.findall(pattern=r".*(?=\sin\s)", string=city)[0]

                        # Remove the unwanted word from city
                        for wo in unwanted_words:
                            city = re.sub(wo, "", city)
                    else:
                        remote = None
                else:
                    remote = None
                
                # salary
                salary = li.xpath(".//div[contains(@class, 'metadata salary-snippet-container')]/div/text()").get()
                
                # Yield the data
                output_dict_listing_page = {
                    "listing_page_url": response.meta["listing_page_url"],
                    "job_title_name": job_title_name,
                    "job_indeed_url": job_indeed_url,
                    "posted_on": posted_on,
                    "company_name": company_name,
                    "city": city,
                    "remote": remote,
                    "salary": salary,
                    "crawled_page_rank": response.meta["crawled_page_rank"],
                    "crawler_name": response.meta["crawler_name"],
                    "zyte_api_automap": {
                        "browserHtml": True,
                        "javascript": True,
                    }
                }

                yield scrapy.Request(
                    url=job_indeed_url,
                    callback=self.parse_job_page,
                    meta=output_dict_listing_page,
                    dont_filter=True
                )
        
    def parse_job_page(self, response):
        logging.info(f"Crawling data from the job page under the URL of {response.meta['crawler_name']} for {response.meta['job_title_name']} in the {response.meta['company_name']} company using this URL --> {response.meta['job_indeed_url']}")
        
        # company_indeed_url
        company_indeed_url = response.xpath("//div[@data-testid='inlineHeader-companyName']//a/@href").get()

        # Salary (sometimes, the salary is not available on the job page, so we need to use the salary from the job page itself)
        if response.meta["salary"] is None:
            salary = response.xpath("//div[@aria-label='Gehalt']/div/ul/li/div/@data-testid | //div[text()='Pay']/following-sibling::div//div[contains(text(), 'a')]//text()").get()
            if salary is not None:
                salary = salary.replace("-tile", "").strip()
        else:
            salary = None

        # Shift and schedule
        shift_and_schedule = response.xpath("//div[@aria-label='Schichten und Arbeitszeiten']/div/ul/li/div/@data-testid | //div[text()='Shift and schedule']/following-sibling::div//div//text()").getall()
        if shift_and_schedule is not None:
            # Remove unwanted keywords from the shift_and_schedule list
            wanted_shift_types = [
                # German
                "Montag bis Freitag", "Wochenendarbeit möglich", "Frühschicht", "Spätschicht", "Tagschicht", "Nachtschicht", "Keine Wochenenden", "8-Stunden-Schicht", "Feiertagsarbeit", "Abendschicht", "Gleitzeit"
            ]
            
            # Collect a list of job types in a list 
            shift_type = [sh.replace("-tile", "") for sh in shift_and_schedule if(sh.replace("-tile", "") in wanted_shift_types)]

            # Join the elements of the list to form a string and separate them with a comma
            shift_and_schedule = ', '.join(shift_type)

        # Job type
        job_type = response.xpath("//div[@aria-label='Anstellungsart']/div/ul/li/div/@data-testid | //div[text()='Job type']//following-sibling::div//text()").getall()
        if job_type is not None:
            # Remove unwanted keywords from the job_type list
            wanted_job_types = [
                # English
                "Full-time", "Permanent", "Contract", "Part-time", "Temporary", "Apprenticeship", "Internship", "Internship / Co-op", "Casual", "Freelance", "Fixed term contract",

                # German
                "Festanstellung", "Teilzeit", "Vollzeit", "Ausbildung", "Befristet", "Praktikum", "Minijob", "Freie Mitarbeit", "Werkstudent", "Befristeter Vertrag",
                "Arbeitnehmerüberlassung"
            ]
            
            # Collect a list of job types in a list 
            job_type = [job.replace("-tile", "") for job in job_type if(job.replace("-tile", "") in wanted_job_types)]

            # Join the elements of the list to form a string and separate them with a comma
            job_type = ', '.join(job_type)

        # Job description
        # job_description = response.css("#jobDescriptionText *::text").getall() # Can also be response.xpath("//div[@id='jobDescriptionText']//text()").getall()
        job_description = response.xpath("//div[@id='jobDescriptionText']//text()").getall()
        if job_description is not None:
            job_description = [job.strip() for job in job_description]
            job_description = [i for i in job_description if i not in [""]]
            job_description = '\n'.join(job_description)

        yield {
            # Job page fields
            "job_title_name": response.meta["job_title_name"],
            "job_type": job_type,
            "shift_and_schedule": shift_and_schedule,
            "company_name": response.meta["company_name"],
            "company_indeed_url": company_indeed_url,
            "city": response.meta["city"].strip() if response.meta["city"] is not None else None,
            "remote": response.meta["remote"],
            "salary": salary,
            "crawled_page_rank": response.meta["crawled_page_rank"],
            "job_page_url": response.meta["job_indeed_url"],
            "posted_on": response.meta["posted_on"],
            "listing_page_url": response.meta["listing_page_url"],
            "job_description": job_description,
            "crawled_timestamp": datetime.now(),
            "crawler_name": response.meta["crawler_name"]
        }

# Run the spider
full_settings_dict = custom_settings_zyte_api_dict.copy()
full_settings_dict.update({
    "FEEDS": {f"{output_file_name_of_indeed_crawler}.json":{"format": "json", "overwrite": True, "encoding": "utf-8"}},
    "LOG_FILE": f"{output_name_of_indeed_logs_file}.log"
})
process = CrawlerProcess(settings=full_settings_dict)
process.crawl(IndeedZyteAPISpider)
process.start()