from datetime import datetime
from utils.db import pg_cursor, close_connection
from helpers.email_service import send_email

# Expected records per website
EXPECTED_COUNTS = {
    "Diamonds Factory": {"table": "stg_price_df_scrape", "count": 304},
    "Brilliant Earth": {"table": "stg_price_brilliantearth_scrape", "count": 150},
    "The Diamond Store": {"table": "stg_price_thediamondstore_scrape", "count": 17},
    "77Diamonds": {"table": "stg_price_77diamonds_scrape", "count": 152},
    "Diamond Heaven": {"table": "stg_diamondheaven_price_scrape", "count": 104},
}

def get_today_report():
    today = datetime.now().strftime("%Y-%m-%d")
    report_data = []

    for website, details in EXPECTED_COUNTS.items():
        query = f"""
            SELECT COUNT(*) 
            FROM {details['table']} 
            WHERE updated_date::date = %s
        """
        pg_cursor.execute(query, (today,))
        count_inserted = pg_cursor.fetchone()[0]
        remaining = details['count'] - count_inserted
        report_data.append((website, details['count'], count_inserted, remaining))

    return report_data


def build_html_report(report_data):
    html = """
    <h3>📊 Daily Records Insertion Report</h3>
    <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; text-align: center;">
        <tr style="background-color: #f2f2f2;">
            <th>Website</th>
            <th>No. of Records Required to be Inserted</th>
            <th>No. of Records Actually Inserted</th>
            <th>Remaining / Total Failed</th>
        </tr>
    """
    for website, required, inserted, remaining in report_data:
        color_inserted = "green" if required == inserted else "red"
        color_remaining = "green" if remaining == 0 else "red"
        html += f"""
        <tr>
            <td>{website}</td>
            <td>{required}</td>
            <td style="color:{color_inserted}; font-weight:bold;">{inserted}</td>
            <td style="color:{color_remaining}; font-weight:bold;">{remaining}</td>
        </tr>
        """
    html += "</table>"
    return html


if __name__ == "__main__":
    try:
        report_data = get_today_report()
        html_report = build_html_report(report_data)

        today = datetime.now().strftime("%Y-%m-%d")
        subject = f"Daily Records Report - {today}"

        send_email(subject, html_report, recipients=None, is_error=False, is_html=True)
        print("✅ Daily report sent successfully.")

    except Exception as e:
        print(f"❌ Failed to generate/send report: {e}")
    finally:
        close_connection()
