from scrapy.crawler import CrawlerProcess
from functions import post_crawling_func
import os

def main_scraper_1():
    # If you are not in indeed/, navigate to it
    if "chris_begin_indeed/indeed" not in os.getcwd():
        os.chdir(os.getcwd() + "/indeed")

    # Run the first crawler that crawls this link --> https://ca.indeed.com/jobs?l=Greater+Toronto+Area%2C+ON&sc=0kf%3Aocc%286YCJB%29%3B&radius=35&sort=date&vjk=f55ce01235a88065
    from indeed.spiders.indeed_zyte_api_1 import IndeedZyteAPI1Spider
    process = CrawlerProcess(settings={
        "FEEDS": {"output_indeed_zyte_api_1.json":{"format": "json", "overwrite": True, "encoding": "utf-8"}},
        "LOG_FILE": "indeed_zyte_api_1.log"
    })
    process.crawl(IndeedZyteAPI1Spider)
    process.start()

    # Run the steps after the crawling
    post_crawling_func(output_json_file="output_indeed_zyte_api_1", crawler_name="crawler_1")

if __name__ == '__main__':
    main_scraper_1()