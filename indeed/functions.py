import re

# HELPER FUNCTIONS
# Format the salary column by creating a function that splits the salary string intro two columns
def salary_type_func(salary):
    if salary is None:
        return None
    else:
        if salary.find("year") != -1:
            return "year"
        elif salary.find("hour") != -1:
            return "hour"
        elif salary.find("month") != -1:
            return "month"
        elif salary.find("week") != -1:
            return "week"
        else:
            return None

# Define a function that return the higher end of the salary
def salary_high_func(salary, salary_type):
    if salary is None:
        return None
    else:
        if salary.find("–") != -1: # Type 1: $55,000–$62,000 a year
            return float(re.findall(pattern=f"(?<=–\$).*(?=\sa\s{salary_type}|\san\s{salary_type})", string=salary)[0].replace(",", ""))
        elif salary.find("From") != -1: # Type 2: From $80,000 a year
            return None
        elif salary.find("Up") != -1: # Type 3: Up to $160,000 a year
            return float(re.findall(pattern=f"(?<=Up\sto\s\$).*(?=\sa\s{salary_type}|\san\s{salary_type})", string=salary)[0].replace(",", ""))
        elif any(x in salary for x in ["-", "From", "Up"]) == False: # Type 4: $150,000 a year
            return float(re.findall(pattern=f"(?<=\$).*(?=\sa\s{salary_type}|\san\s{salary_type})", string=salary)[0].replace(",", ""))
        else:
            return None

# Define a function that returns the lower end of the salary
def salary_low_func(salary, salary_type):
    if salary is None:
        return None
    else:
        if salary.find("–") != -1: # Type 1: $55,000–$62,000 a year
            return float(re.findall(pattern="(?<=\$).*(?=\–\$)", string=salary)[0].replace(",", ""))
        elif salary.find("From") != -1: # Type 2: From $80,000 a year
            return float(re.findall(pattern=f"(?<=From\s\$).*(?=\sa\s{salary_type}|\san\s{salary_type})", string=salary)[0].replace(",", ""))
        elif salary.find("Up") != -1: # Type 3: Up to $160,000 a year
            return None
        elif any(x in salary for x in ["-", "From", "Up"]) is False: # Type 4: $150,000 a year
            return float(re.findall(pattern=f"(?<=\$).*(?=\sa\s{salary_type}|\san\s{salary_type})", string=salary)[0].replace(",", ""))
        else:
            return None

# Define a function that loops through the entire company list and searches for industry matches
def company_name_finder_func(x, companies_df):
    for idx, i in enumerate(companies_df["company_name"]):
        # The first type of match is an "exact_match"
        if x.lower() == i.lower():
            return companies_df.iloc[idx]["industry"], "exact_match", idx
        
        # If no exact match is found, search for a partial match
        elif x.lower() in i.lower():
            return companies_df.iloc[idx]["industry"], "partial_match", idx
    
    # If all the company names in the for loop are exhausted and no match is found, return "no_match"
    return None, "no_match", idx

def post_crawling_func(crawler_name):
    import json
    import pandas as pd
    import os
    from inputs import (
        output_file_name_of_indeed_crawler,
        output_file_name_of_google_crawler,
        output_name_of_indeed_logs_file
    )
    from google.cloud import bigquery
    from google.oauth2 import service_account
    import yagmail
    from datetime import datetime
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s  - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        filename=output_name_of_indeed_logs_file,

    )

    # Open the JSON file containing the output and format the data
    with open(f"{output_file_name_of_indeed_crawler}.json", mode="r", encoding="utf-8") as f:
        df = json.load(f)
        df = pd.DataFrame(df)
        f.close()
    
    # Apply the salary_type_func
    logging.info("Applying the salary_type func")
    df["salary_type"] = df["salary"].apply(salary_type_func)

    # Create the columns containing the salary bands
    logging.info("Create the columns containing the salary bands")
    df["salary_low"] = df[["salary", "salary_type"]].apply(lambda x: salary_low_func(*x), axis=1)
    df["salary_high"] = df.apply(lambda x: salary_high_func(x["salary"], x["salary_type"]), axis=1)

    # Change the data type of crawled_timestamp to datetime
    df["crawled_timestamp"] = df["crawled_timestamp"].apply(lambda x: pd.to_datetime(x))

    # Add another field to identify the crawler
    df["crawler_name"] = crawler_name

    ###---------------------------END OF OUTPUT INGESTION FROM INDEED PART---------------------------###
    
    # Open the JSON file containing the phone numbers
    with open(f"{output_file_name_of_google_crawler}.json", mode="r", encoding="utf-8") as f:
        df_phone_numbers = json.load(f)
        df_phone_numbers = pd.DataFrame(df_phone_numbers)
        f.close()
    
    # Merge the phone numbers with the main data frame
    logging.info("Merging the phone numbers with the main data frame")
    df = pd.merge(left=df, right=df_phone_numbers, on="company_name", how="left")

    ###-------------------------------END OF PHONE NUMBER ADDITION PART------------------------------###

    # Add the company's industry to the data frame based on the company's name
    # First, read the CSV file containing the company names and indstries
    logging.info("Opening the company_industry_list CSV file and applying some cleaning rules to the company_name column")
    companies = pd.read_csv("company_industry_list.csv")

    # Filter out NULL values
    companies = companies[companies["company_name"].notnull()]

    # Add a new column displaying the company's name without non-ascii characters
    companies["company_name_clean"] = companies["company_name"].apply(lambda x: x.encode("ascii", "ignore").decode())

    # Filter out rows where company_name_clean == company_name. Those rows have ONLY ASCII characters
    companies = companies[companies["company_name"] == companies["company_name_clean"]].sort_values(by="company_name").reset_index(drop=True)

    logging.info("Creating three new columns industry, industry_match_type, and industry_match_idx and move the timestamp column to the very end of the data frame")
    # Create a new column called "industry". The second apply function is to pick the "industry" from the tuple produced by the company_name_finder_func
    df["industry"] = df.apply(lambda x: company_name_finder_func(x["company_name"], companies), axis=1).apply(lambda x: x[0])

    # Create a new column called "industry_match_type". The second apply function is to pick the "industry_match_type" from the tuple produced by the company_name_finder_func
    df["industry_match_type"] = df.apply(lambda x: company_name_finder_func(x["company_name"], companies), axis=1).apply(lambda x: x[1])

    # Create a new column called "industry_match_idx". The second apply function is to pick the "industry_match_idx" from the tuple produced by the company_name_finder_func
    df["industry_match_idx"] = df.apply(lambda x: company_name_finder_func(x["company_name"], companies), axis=1).apply(lambda x: x[2])

    # Move the timestamp column to the very end of the data frame
    df[[col for col in df if col not in ["crawled_timestamp"]] + ["crawled_timestamp"]]

    ###--------------------------------END OF INDUSTRY ADDITION PART--------------------------------###

    logging.info("Uploading results to BQ")
    # Upload the results to bigquery
    # First, set the credentials
    key_path_local = os.getcwd() + "/bq_credentials.json"
    credentials = service_account.Credentials.from_service_account_file(
        key_path_local, scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )

    # Now, instantiate the client and upload the table to BigQuery
    client = bigquery.Client(project="web-scraping-371310", credentials=credentials)
    job_config = bigquery.LoadJobConfig(
        schema = [
            # Fields from the main indeed crawler
            bigquery.SchemaField("job_title_name", "STRING"),
            bigquery.SchemaField("job_type", "STRING"),
            bigquery.SchemaField("company_name", "STRING"),
            bigquery.SchemaField("company_indeed_url", "STRING"),
            bigquery.SchemaField("city", "STRING"),
            bigquery.SchemaField("remote", "STRING"),
            bigquery.SchemaField("salary", "STRING"),
            bigquery.SchemaField("crawled_page_rank", "INT64"), 
            bigquery.SchemaField("job_page_url", "STRING"),
            bigquery.SchemaField("listing_page_url", "STRING"),
            bigquery.SchemaField("job_description", "STRING"),
            bigquery.SchemaField("salary_type", "STRING"),
            bigquery.SchemaField("salary_low", "FLOAT64"),
            bigquery.SchemaField("salary_high", "FLOAT64"),
            bigquery.SchemaField("crawler_name", "STRING"),
            
            # Fields from Google
            bigquery.SchemaField("search_query", "STRING"),
            bigquery.SchemaField("phone_number", "STRING"),
            
            # Fields from the Excel file containing the industry of each company name
            bigquery.SchemaField("industry", "STRING"),
            bigquery.SchemaField("industry_match_type", "STRING"),
            bigquery.SchemaField("industry_match_idx", "INT64"),

            # Crawled timestamp
            bigquery.SchemaField("crawled_timestamp", "TIMESTAMP"),
        ]
    )
    job_config.write_disposition = bigquery.WriteDisposition.WRITE_APPEND

    # Upload the table
    client.load_table_from_dataframe(
        dataframe=df,
        destination="web-scraping-371310.crawled_datasets.chris_indeed_workflow",
        job_config=job_config
    ).result()

    # Step 16: Send success E-mail
    logging.info("Sending success E-mail\n")
    yag = yagmail.SMTP("omarmoataz6@gmail.com", oauth2_file=os.getcwd() + "/email_authentication.json")
    contents = [
        f"This is an automatic notification to inform you that the Indeed {crawler_name} ran successfully"
    ]
    yag.send(["omarmoataz6@gmail.com"], f"The Indeed {crawler_name} ran successfully at {datetime.now()} CET", contents)