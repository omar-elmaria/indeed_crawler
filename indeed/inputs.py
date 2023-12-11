import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define custom settings for the spider
custom_settings_dict = {
    "FEED_EXPORT_ENCODING": "utf-8", # UTF-8 deals with all types of characters
    "RETRY_TIMES": 3, # Retry failed requests up to 3 times
    "AUTOTHROTTLE_ENABLED": False, # Disables the AutoThrottle extension (recommended to be used if you are not using proxy services)
    "RANDOMIZE_DOWNLOAD_DELAY": False, # Should not be used with proxy services. If enabled, Scrapy will wait a random amount of time (between 0.5 * DOWNLOAD_DELAY and 1.5 * DOWNLOAD_DELAY) while fetching requests from the same website
    "CONCURRENT_REQUESTS": 5, # The maximum number of concurrent (i.e. simultaneous) requests that will be performed by the Scrapy downloader
    "DOWNLOAD_TIMEOUT": 60, # Setting the timeout parameter to 60 seconds as per the ScraperAPI documentation
    "ROBOTSTXT_OBEY": False # Don't obey the Robots.txt rules
}

custom_settings_zyte_api_dict = custom_settings_dict.copy()
custom_settings_zyte_api_dict.update({
    "DOWNLOAD_HANDLERS": {
        "http": "scrapy_zyte_api.ScrapyZyteAPIDownloadHandler",
        "https": "scrapy_zyte_api.ScrapyZyteAPIDownloadHandler",
    },
    "DOWNLOADER_MIDDLEWARES": {
        "scrapy_zyte_api.ScrapyZyteAPIDownloaderMiddleware": 1000,
    },
    "REQUEST_FINGERPRINTER_CLASS": "scrapy_zyte_api.ScrapyZyteAPIRequestFingerprinter",
    "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
    "ZYTE_API_KEY": os.getenv("ZYTE_API_KEY"),
    "ZYTE_API_LOG_REQUESTS": True,
    "ZYTE_API_TRANSPARENT_MODE": True,
    "ZYTE_API_SKIP_HEADERS": ["Cookie", "User-Agent"],
    "ZYTE_API_RETRY_POLICY": "retry_policies.CUSTOM_RETRY_POLICY"
})

# Scraper API prefix and suffix
prefix = f"https://api.scraperapi.com/?api_key={os.getenv(key='SCRAPER_API_KEY')}&url="
suffix = ""

# Global Inputs
num_listings_per_page = 15
page_index_step = 10
page_index_max = 620
output_file_name_of_indeed_crawler = "output_indeed_zyte_api"
output_file_name_of_google_crawler = "output_phone_numbers"
output_name_of_indeed_logs_file = "indeed_zyte_api"