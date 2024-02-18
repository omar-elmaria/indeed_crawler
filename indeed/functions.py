import re

# HELPER FUNCTIONS
# Format the salary column by creating a function that splits the salary string intro two columns
def salary_type_func(salary, domain):
    if salary is None:
        return None
    else:
        if re.findall("year|jahr", salary.lower()) != []:
            if domain == "ca":
                return "year"
            elif domain == "de":
                return "jahr"
        elif re.findall("hour|stunde", salary.lower()) != []:
            if domain == "ca":
                return "hour"
            elif domain == "de":
                return "stunde"
        elif re.findall("month|monat", salary.lower()) != []:
            if domain == "ca":
                return "month"
            elif domain == "de":
                return "monat"
        elif re.findall("week|woche", salary.lower()) != []:
            if domain == "ca":
                return "week"
            elif domain == "de":
                return "woche"
        elif re.findall("day|tag", salary.lower()) != []:
            if domain == "ca":
                return "tag"
            elif domain == "de":
                return "day"
        else:
            return None

# Define a function that return the higher end of the salary
def salary_high_func(salary, salary_type, indeed_domain):
    if salary is None:
        return None
    else:
        if indeed_domain == "ca":
            if salary.find("–") != -1: # Type 1: $55,000–$62,000 a year
                return float(re.findall(pattern=f"(?<=–\$).*(?=\sa\s{salary_type}|\san\s{salary_type})", string=salary)[0].replace(",", ""))
            elif salary.find("From") != -1: # Type 2: From $80,000 a year
                return None
            elif salary.find("Up") != -1: # Type 3: Up to $160,000 a year
                return float(re.findall(pattern=f"(?<=Up\sto\s\$).*(?=\sa\s{salary_type}|\san\s{salary_type})", string=salary)[0].replace(",", ""))
            elif any(x in salary for x in ["–", "From", "Up"]) == False: # Type 4: $150,000 a year
                return float(re.findall(pattern=f"(?<=\$).*(?=\sa\s{salary_type}|\san\s{salary_type})", string=salary)[0].replace(",", ""))
            else:
                return None
        elif indeed_domain == "de":
            if salary.find("–") != -1: # Type 1: 28.500 € – 37.000 € pro Jahr
                return float(re.findall(pattern=f"(?<=–\s).*(?=\s€\spro\s{salary_type})", string=salary.lower())[0].replace(",", ".").replace(".", ""))
            elif salary.lower().find("ab") != -1: # Type 2: Ab 40.000 € pro Jahr
                return None
            elif salary.lower().find("bis zu") != -1: # Type 3: Bis 60.000 € pro Jahr
                return float(re.findall(pattern=f"(?<=bis\szu\s).*(?=\s€\spro\s{salary_type})", string=salary.lower())[0].replace(",", ".").replace(".", ""))
            elif any(x in salary.lower() for x in ["–", "ab", "bis zu"]) == False: # Type 4: 39.000 € pro Jahr
                return float(re.findall(pattern=f".*(?=\s€\spro\s{salary_type})", string=salary.lower())[0].replace(",", ".").replace(".", ""))
            else:
                return None
        else:
            return None

# Define a function that returns the lower end of the salary
def salary_low_func(salary, salary_type, indeed_domain):
    if salary is None:
        return None
    else:
        if indeed_domain == "ca":
            if salary.find("–") != -1: # Type 1: $55,000–$62,000 a year
                return float(re.findall(pattern="(?<=\$).*(?=\–\$)", string=salary)[0].replace(",", ""))
            elif salary.find("From") != -1: # Type 2: From $80,000 a year
                return float(re.findall(pattern=f"(?<=From\s\$).*(?=\sa\s{salary_type}|\san\s{salary_type})", string=salary)[0].replace(",", ""))
            elif salary.find("Up") != -1: # Type 3: Up to $160,000 a year
                return None
            elif any(x in salary for x in ["–", "From", "Up"]) is False: # Type 4: $150,000 a year
                return float(re.findall(pattern=f"(?<=\$).*(?=\sa\s{salary_type}|\san\s{salary_type})", string=salary)[0].replace(",", ""))
            else:
                return None
        elif indeed_domain == "de":
            if salary.find("–") != -1: # Type 1: 28.500 € – 37.000 € pro Jahr
                return float(re.findall(pattern=f".*(?=\s€\s–)", string=salary)[0].replace(",", ".").replace(".", ""))
            elif salary.lower().find("ab") != -1: # Type 2: Ab 40.000 € pro Jahr
                return float(re.findall(pattern=f"(?<=ab\s).*(?=\s€\spro\s{salary_type})", string=salary.lower())[0].replace(",", ".").replace(".", ""))
            elif salary.lower().find("bis zu") != -1: # Type 3: Bis 60.000 € pro Jahr
                return None
            elif any(x in salary.lower() for x in ["–", "ab", "bis zu"]) == False: # Type 4: 39.000 € pro Jahr
                return float(re.findall(pattern=f".*(?=\s€\spro\s{salary_type})", string=salary.lower())[0].replace(",", ".").replace(".", ""))
            else:
                return None
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

def post_crawling_func():
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
    import gspread
    import yagmail
    from datetime import datetime
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s  - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        filename=f"{output_name_of_indeed_logs_file}.log",

    )

    # Open the JSON file containing the output and format the data
    with open(f"{output_file_name_of_indeed_crawler}.json", mode="r", encoding="utf-8") as f:
        df = json.load(f)
        df = pd.DataFrame(df)
        f.close()
    
    # Extract the domain from the job_page_url column
    df["domain"] = df["job_page_url"].apply(lambda x: re.findall("(?<=https:\/\/).*(?=\.indeed)", x)[0] if x is not None else None)
    
    # Apply the salary_type_func
    logging.info("Applying the salary_type func")
    df["salary_type"] = df.apply(lambda x: salary_type_func(x["salary"], x["domain"]), axis=1)

    # Create the columns containing the salary bands
    logging.info("Create the columns containing the salary bands")
    df["salary_low"] = df.apply(lambda x: salary_low_func(x["salary"], x["salary_type"], x["domain"]), axis=1)
    df["salary_high"] = df.apply(lambda x: salary_high_func(x["salary"], x["salary_type"], x["domain"]), axis=1)

    # Add a new column called "plz" that contains the postal code extracted from the "city" column
    df["plz"] = df["city"].apply(lambda x: re.findall("\d+", x) if x is not None else None).apply(lambda x: x[0] if x != [] and x is not None else None)

    # Extract the city name from the composite string and remove any extra spaces from the "city" column
    df["city"] = df["city"].apply(lambda x: re.findall("\D+", x) if x is not None else None).apply(lambda x: x[0].strip() if x != [] and x is not None else None)

    # Change the data type of crawled_timestamp to datetime
    df["crawled_timestamp"] = df["crawled_timestamp"].apply(lambda x: pd.to_datetime(x))

    ###---------------------------END OF OUTPUT INGESTION FROM INDEED PART---------------------------###
    
    # Open the JSON file containing the phone numbers
    with open(f"{output_file_name_of_google_crawler}.json", mode="r", encoding="utf-8") as f:
        df_phone_numbers = json.load(f)
        df_phone_numbers = pd.DataFrame(df_phone_numbers)
        f.close()
    
    # Open the master JSON file containing the phone numbers
    with open(f"{output_file_name_of_google_crawler}_master.json", mode="r", encoding="utf-8") as f:
        df_phone_numbers_master = json.load(f)
        df_phone_numbers_master = pd.DataFrame(df_phone_numbers_master)
        f.close()
    
    # Merge the phone numbers with the main data frame
    logging.info("Merging the phone numbers with the main data frame")
    try:
        df = pd.merge(left=df, right=df_phone_numbers, on="company_name", how="left")
    except KeyError as e:
        df = pd.merge(left=df, right=df_phone_numbers_master, on="company_name", how="left")

    ###-------------------------------END OF PHONE NUMBER ADDITION PART------------------------------###

    # Add the company's industry to the data frame based on the company's name
    # First, read the Google Sheet containing the company names and indstries
    logging.info("Opening the company_industry_list Google Sheet and applying some cleaning rules to the company_name column")
    SHEET_ID = '1uxieppTDNYfHLOJ5F1NiJF5SRQTAAX7r3Y5NNJlcxLM'
    SHEET_NAME = 'companies'
    gc = gspread.service_account(os.path.expanduser("~") + "/bq_credentials.json")
    spreadsheet = gc.open_by_key(SHEET_ID)
    worksheet = spreadsheet.worksheet(SHEET_NAME)
    rows = worksheet.get_all_records()
    companies = pd.DataFrame(rows)

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

    # Move the timestamp and domain columns to the very end of the data frame
    df[[col for col in df if col not in ["crawled_timestamp", "crawler_name", "domain"]] + ["crawled_timestamp", "crawler_name", "domain"]]

    ###--------------------------------END OF INDUSTRY ADDITION PART--------------------------------###

    logging.info("Uploading results to BQ")
    # Upload the results to bigquery
    # First, set the credentials
    key_path_local = os.path.expanduser("~") + "/bq_credentials.json"
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
            bigquery.SchemaField("shift_and_schedule", "STRING"),
            bigquery.SchemaField("company_name", "STRING"),
            bigquery.SchemaField("company_indeed_url", "STRING"),
            bigquery.SchemaField("city", "STRING"),
            bigquery.SchemaField("plz", "STRING"),
            bigquery.SchemaField("remote", "STRING"),
            bigquery.SchemaField("salary", "STRING"),
            bigquery.SchemaField("crawled_page_rank", "INT64"), 
            bigquery.SchemaField("job_page_url", "STRING"),
            bigquery.SchemaField("listing_page_url", "STRING"),
            bigquery.SchemaField("job_description", "STRING"),
            bigquery.SchemaField("salary_type", "STRING"),
            bigquery.SchemaField("salary_low", "FLOAT64"),
            bigquery.SchemaField("salary_high", "FLOAT64"),
            
            # Fields from Google
            bigquery.SchemaField("search_query", "STRING"),
            bigquery.SchemaField("phone_number", "STRING"),
            
            # Fields from the Excel file containing the industry of each company name
            bigquery.SchemaField("industry", "STRING"),
            bigquery.SchemaField("industry_match_type", "STRING"),
            bigquery.SchemaField("industry_match_idx", "INT64"),

            # Crawled timestamp
            bigquery.SchemaField("crawled_timestamp", "TIMESTAMP"),
            bigquery.SchemaField("crawler_name", "STRING"),
            bigquery.SchemaField("domain", "STRING"),
        ]
    )
    job_config.write_disposition = bigquery.WriteDisposition.WRITE_APPEND

    # Upload the table
    client.load_table_from_dataframe(
        dataframe=df,
        destination="web-scraping-371310.crawled_datasets.laura_indeed_data",
        job_config=job_config
    ).result()

    # Step 16: Send success E-mail
    logging.info("Sending success E-mail\n")
    yag = yagmail.SMTP("omarmoataz6@gmail.com", smtp_ssl=False, oauth2_file=os.path.expanduser("~") + "/email_authentication.json")
    contents = [
        f"This is an automatic notification to inform you that the Indeed crawler ran successfully"
    ]
    yag.send(["omarmoataz6@gmail.com", "laura.scherer@circuculture.com"], f"The Indeed crawler ran successfully at {datetime.now()} CET", contents)