import pandas as pd
from email_service import send_email

# Load Excel file
df = pd.read_excel("price_comparison.xlsx")

# Convert DataFrame to HTML (with basic table styles for email readability)
html_table = df.to_html(index=False, border=1)

subject = "Price Comparison Report"
body = f"""
<html>
  <body>
    <p>Hello,<br><br>
       Please find below the latest price comparison report:<br><br>
    </p>
    {html_table}
    <p><br>Regards,<br>Automation Bot</p>
  </body>
</html>
"""

# Send as HTML
send_email(subject, body, is_html=True)

print("✅ Email with HTML table sent")
