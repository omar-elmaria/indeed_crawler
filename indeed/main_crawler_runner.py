from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
import os
from inputs import (
    output_file_name_of_indeed_crawler,
    output_file_name_of_google_crawler,
    output_name_of_indeed_logs_file
)

def main():
    # If you are not in indeed/, navigate to it
    if "indeed_crawler\\indeed" not in os.getcwd():
        os.chdir(os.getcwd() + "/indeed")
    
    # Configure logging
    configure_logging()

    # Define three Crawler runners, one for each spider
    runner_indeed = CrawlerRunner(settings={
        "FEEDS": {f"{output_file_name_of_indeed_crawler}.json":{"format": "json", "overwrite": True, "encoding": "utf-8"}},
        "LOG_FILE": f"{output_name_of_indeed_logs_file}.log"
    })
    runner_google = CrawlerRunner(settings={
        "FEEDS": {f"{output_file_name_of_google_crawler}.json":{"format": "json", "overwrite": True, "encoding": "utf-8"}},
        "LOG_FILE": f"{output_name_of_indeed_logs_file}.log"
    })

    @defer.inlineCallbacks
    def crawl():
        # Run the first crawler that crawls this link --> https://ca.indeed.com/jobs?l=Greater+Toronto+Area%2C+ON&sc=0kf%3Aocc%286YCJB%29%3B&radius=35&sort=date&vjk=f55ce01235a88065
        from indeed.spiders.indeed_zyte_api import IndeedZyteAPISpider
        yield runner_indeed.crawl(IndeedZyteAPISpider)

        # Run the second crawler that crawls the phone numbers from Google
        from indeed.spiders.google_company_phone_number import GoogleSpider
        yield runner_google.crawl(GoogleSpider)

        # Stop the reactor
        reactor.stop()

    # Run the crawl() function
    crawl()

if __name__ == '__main__':
    main()