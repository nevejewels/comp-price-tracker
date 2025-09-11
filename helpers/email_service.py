import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Email configuration
EMAIL_CONFIG = {
    'sender': os.getenv('EMAIL_SENDER'),
    'password': os.getenv('EMAIL_PASSWORD'),
    'recipients': os.getenv('EMAIL_RECIPIENTS').split(','),
    'smtp_server': os.getenv('EMAIL_SMTP_SERVER'),
    'smtp_port': int(os.getenv('EMAIL_SMTP_PORT'))
}

# def send_email(subject, body, is_error=False):
#     """Send email notification with the given subject and body."""
#     try:
#         msg = MIMEMultipart()
#         msg['From'] = EMAIL_CONFIG['sender']
#         msg['To'] = ", ".join(EMAIL_CONFIG['recipients'])
#         msg['Subject'] = subject

#         # Format error messages differently
#         if is_error:
#             body = f"🚨 ERROR ALERT 🚨\n\n{body}"
#         else:
#             body = f"✅ SCRAPER NOTIFICATION ✅\n\n{body}"

#         msg.attach(MIMEText(body, 'plain'))

#         with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
#             server.starttls()
#             server.login(EMAIL_CONFIG['sender'], EMAIL_CONFIG['password'])
#             server.send_message(msg)
#     except Exception as e:
#         print(f"Failed to send email: {e}")
#         # Log this failure if you have a logging system

def send_email(subject, body, is_error=False, is_html=False):
    """Send email notification with the given subject and body."""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender']
        msg['To'] = ", ".join(EMAIL_CONFIG['recipients'])
        msg['Subject'] = subject

        if is_error:
            body = f"🚨 ERROR ALERT 🚨<br><br>{body}"
        else:
            body = f"✅ SCRAPER NOTIFICATION ✅<br><br>{body}"

        if is_html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['sender'], EMAIL_CONFIG['password'])
            server.send_message(msg)
    except Exception as e:
        print(f"❌ Failed to send email: {e}")


def send_error_email(website_name, error, url=None, row_data=None):
    """Send an error notification email with details about the failure."""
    error_trace = traceback.format_exc()
    today = datetime.now().strftime("%Y-%m-%d")  # Format: YYYY-MM-DD
    subject = f"Scraper Error Alert - {today}"

    # body = f"Error occurred during scraping for {website_name}:\n\n"
    # body += f"Error: {str(error)}\n\n"
    # body += f"Traceback:\n{error_trace}\n\n"

    # Get only short error (1–2 lines)
    short_error = "".join(traceback.format_exception_only(type(error), error)).strip()

    body = f"Error occurred during scraping for {website_name}:\n\n"
    body += f"Error: {short_error}\n\n"

    if url:
        body += f"Failed URL: {url}\n"
    if row_data:
        body += f"Failed row data: {row_data}\n"
    
    send_email(subject, body, is_error=True)

def send_completion_email(website_name, total_scraped, total_failed, execution_time, total_input_count, total_scraped_count):
    """Send a summary email when all scraping is complete."""
    today = datetime.now().strftime("%Y-%m-%d")  # Format: YYYY-MM-DD
    subject = f"Scraper Job Completed - {today}"

    body = f"Scraping job has completed for {website_name}.\n\n"
    body += f"Total input items: {total_input_count}\n"
    body += f"Total items scraped: {total_scraped_count}\n"
    body += f"Total items scraped this session: {total_scraped}\n"
    body += f"Total items failed this session: {total_failed}\n"
    body += f"Total execution time this session: {execution_time}\n"
    send_email(subject, body)

# website_name = "thediamondstore"
# total_scraped = 17
# total_failed = 0
# execution_time = "03:23:65"
# total_input_count = 17
# total_scraped_count = 17
# send_completion_email(website_name, total_scraped, total_failed, execution_time, total_input_count, total_scraped_count)
