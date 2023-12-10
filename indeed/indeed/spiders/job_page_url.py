import scrapy
from inputs import (
    custom_settings_zyte_api_dict,
    output_name_of_indeed_logs_file
)
import logging
from scrapy.crawler import CrawlerProcess

class IndeedJobPageSpider(scrapy.Spider):
    name = 'indeed_job_page'
    
    def start_requests(self):
        # Insert a new line for logging
        logging.info("\n")

        urls = [
            "https://de.indeed.com/viewjob?jk=e00701f74a56b454&from=serp&vjs=3",
            "https://de.indeed.com/viewjob?cmp=Avvale&t=Sap-consultant&jk=d034fd7539b0c379&xpse=SoC567I3Hqc2O7RJpp0LbzkdCdPP&xkcb=SoAJ67M3Hqc2ff2eNh0FbzkdCdPP&vjs=3"
        ]

        for i in urls:
            yield scrapy.Request(
                url=i,
                callback=self.parse_job_page,
                meta={"base_url": i}
            )

    def parse_job_page(self, response):        
        # company_indeed_url
        company_indeed_url = response.xpath("//div[@data-testid='inlineHeader-companyName']//a/@href").get()

        # Salary
        salary = response.xpath("//div[text()='Gehalt']/following-sibling::div//div[contains(text(), 'pro')]//text() | //div[text()='Pay']/following-sibling::div//div[contains(text(), 'a')]//text()").get()

        # Shift and schedule
        shift_and_schedule = response.xpath("//div[text()='Schichten und Arbeitszeiten']/following-sibling::div//div//text() | //div[text()='Shift and schedule']/following-sibling::div//div//text()").getall()
        if shift_and_schedule is not None:
            # Remove unwanted keywords from the shift_and_schedule list
            wanted_shift_types = [
                # German
                "Montag bis Freitag", "Wochenendarbeit möglich", "Frühschicht", "Spätschicht", "Tagschicht", "Nachtschicht", "Keine Wochenenden", "8-Stunden-Schicht", "Feiertagsarbeit", "Abendschicht", "Gleitzeit"
            ]
            
            # Collect a list of job types in a list 
            shift_type = [sh for sh in shift_and_schedule if(sh in wanted_shift_types)]

            # Join the elements of the list to form a string and separate them with a comma
            shift_and_schedule = ', '.join(shift_type)

        # Job type
        job_type = response.xpath("//div[text()='Anstellungsart']//following-sibling::div//text() | //div[text()='Job type']//following-sibling::div//text()").getall()
        if job_type is not None:
            # Remove unwanted keywords from the job_type list
            wanted_job_types = [
                # English
                "Full-time", "Permanent", "Contract", "Part-time", "Temporary", "Apprenticeship", "Internship", "Internship / Co-op", "Casual", "Freelance", "Fixed term contract",

                # German
                "Festanstellung", "Teilzeit", "Vollzeit", "Ausbildung", "Befristet", "Praktikum", "Minijob", "Freie Mitarbeit"
            ]
            
            # Collect a list of job types in a list 
            job_type = [job for job in job_type if(job in wanted_job_types)]

            # Join the elements of the list to form a string and separate them with a comma
            job_type = ', '.join(job_type)

        # Job description
        job_description = response.css("#jobDescriptionText *::text").getall() # Can also be response.xpath("//div[@id='jobDescriptionText']//text()").getall()
        if job_description is not None:
            job_description = [job.strip() for job in job_description]
            job_description = [i for i in job_description if i not in [""]]
            job_description = '\n'.join(job_description)

        yield {
            # Job page fields
            "shift_and_schedule": shift_and_schedule,
            "company_indeed_url": company_indeed_url,
            "salary": salary,
            "job_type": job_type,
            "job_page_url": response.meta["base_url"],
            "job_description": job_description,
        }

# Run the spider
full_settings_dict = custom_settings_zyte_api_dict.copy()
full_settings_dict.update({
    "FEEDS": {"job_page_output.json":{"format": "json", "overwrite": True, "encoding": "utf-8"}},
    "LOG_FILE": f"{output_name_of_indeed_logs_file}.log"
})
process = CrawlerProcess(settings=full_settings_dict)
process.crawl(IndeedJobPageSpider)
process.start()