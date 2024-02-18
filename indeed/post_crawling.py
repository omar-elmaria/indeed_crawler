from functions import post_crawling_func
import logging
from datetime import datetime
import yagmail
import os

try:
    post_crawling_func()
except Exception as err:
    # Print an error message
    error_message = f"An error occurred while running the post_crawling function. Go check the error logs at timestamp {datetime.now()}"
    logging.exception(err)
    
    # Send an E-mail notifying that the error occurred
    yag = yagmail.SMTP("omarmoataz6@gmail.com", smtp_ssl=False, oauth2_file=os.path.expanduser("~") + "/email_authentication.json")
    contents = [
        error_message
    ]
    yag.send(["omarmoataz6@gmail.com"], error_message, contents)