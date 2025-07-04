import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback

# Email configuration
EMAIL_CONFIG = {
    'sender': 'rahul.gupta@navgrahaa.com',
    'password': 'sqsv odau pbmj tgkv',
    'recipients': ['rahul.gupta@navgrahaa.com', 'shilwant.gupta@navgrahaa.com'],
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587
}

def send_email(subject, body, is_error=False):
    """Send email notification with the given subject and body."""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender']
        msg['To'] = ", ".join(EMAIL_CONFIG['recipients'])
        msg['Subject'] = subject

        # Format error messages differently
        if is_error:
            body = f"🚨 ERROR ALERT 🚨\n\n{body}"
        else:
            body = f"✅ SCRAPER NOTIFICATION ✅\n\n{body}"

        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['sender'], EMAIL_CONFIG['password'])
            server.send_message(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")
        # Log this failure if you have a logging system

def send_error_email(website_name, error, url=None, row_data=None):
    """Send an error notification email with details about the failure."""
    error_trace = traceback.format_exc()
    subject = f"Scraper Error Alert - {website_name}"

    body = f"Error occurred during scraping for {website_name}:\n\n"
    body += f"Error: {str(error)}\n\n"
    body += f"Traceback:\n{error_trace}\n\n"
    
    if url:
        body += f"Failed URL: {url}\n"
    if row_data:
        body += f"Failed row data: {row_data}\n"
    
    send_email(subject, body, is_error=True)

def send_completion_email(website_name, total_scraped, total_failed, execution_time, total_input_count, total_scraped_count):
    """Send a summary email when all scraping is complete."""
    subject = f"Scraper Job Completed - {website_name}"

    body = f"Scraping job has completed for {website_name}.\n\n"
    body += f"Total input items: {total_input_count}\n"
    body += f"Total items scraped: {total_scraped_count}\n"
    body += f"Total items scraped this session: {total_scraped}\n"
    body += f"Total items failed this session: {total_failed}\n"
    body += f"Total execution time this session: {execution_time}\n"
    send_email(subject, body)