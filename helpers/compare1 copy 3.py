import pandas as pd
from email_service import send_email
from sqlalchemy import create_engine

# Your existing database query code
engine = create_engine("postgresql+psycopg2://briqpay:briqpay111@178.79.182.27/briqpay")

query = """
SELECT
    website,
    collection_no,
    DATE(updated_date) AS price_date,
    ROUND(AVG(final_price)::numeric, 2) AS avg_final_price
FROM (
    SELECT website, collection_no, updated_date, final_price FROM stg_price_df_scrape
    UNION ALL
    SELECT website, collection_no, updated_date, final_price FROM stg_price_brilliantearth_scrape
    UNION ALL
    SELECT website, collection_no, updated_date, final_price FROM stg_price_thediamondstore_scrape
    UNION ALL
    SELECT website, collection_no, updated_date, final_price FROM stg_price_77diamonds_scrape
    UNION ALL
    SELECT website, collection_no, updated_date, final_price FROM stg_diamondheaven_price_scrape
) AS combined
WHERE updated_date::date IN (
    CURRENT_DATE - INTERVAL '1 day',
    CURRENT_DATE - INTERVAL '2 day'
)
GROUP BY website, collection_no, DATE(updated_date)
ORDER BY website, collection_no, price_date;
"""

df = pd.read_sql(query, engine)
print(f"Total rows fetched: {df.shape[0]}")
print(f"Unique websites: {df['website'].unique().tolist()}")

# Your existing data processing code
pivot_df = df.pivot_table(
    index=["collection_no", "price_date"],
    columns="website",
    values="avg_final_price"
).reset_index()

unique_dates = sorted(df["price_date"].unique())
if len(unique_dates) < 2:
    print("Not enough dates in query result")
    exit()

day_before, yesterday = unique_dates

y_df = pivot_df[pivot_df["price_date"] == yesterday].set_index("collection_no")
d_df = pivot_df[pivot_df["price_date"] == day_before].set_index("collection_no")

merged = y_df.join(d_df, lsuffix="_yesterday", rsuffix="_daybefore", how="outer")

# Check what columns are available after merging
print("Available columns after merge:", merged.columns.tolist())
print("Sample of merged data:")
print(merged.head())

def calc_pct(col, base_col):
    return ((merged[col] - merged[base_col]) / merged[base_col]) * 100

comparison = pd.DataFrame({
    "DF Avg Price": merged["diamondsfactory_yesterday"],
    "Brilliant Earth %": calc_pct("brilliantearth_yesterday", "diamondsfactory_yesterday"),
    "The Diamond Store %": calc_pct("thediamondstore_yesterday", "diamondsfactory_yesterday"),
    "77 Diamonds %": calc_pct("77diamonds_yesterday", "diamondsfactory_yesterday"),
    "Diamond Heaven %": calc_pct("diamond-heaven_yesterday", "diamondsfactory_yesterday"),
}, index=merged.index)

comparison = comparison.round(2)

# --- NEW: Function to apply the same color logic for HTML ---
def get_cell_color(val):
    """Return background color based on value"""
    if pd.isna(val):
        return ""
    if val > 5:
        return "background-color: #ff4444; color: white;"  # Red for > 5%
    elif val < 0:
        return "background-color: #44ff44; color: white;"  # Green for < 0%
    return ""

# --- Apply styling to the comparison dataframe ---
def highlight(val):
    return get_cell_color(val)

styled = comparison.style.map(
    highlight, subset=["Brilliant Earth %", "The Diamond Store %", "77 Diamonds %", "Diamond Heaven %"]
).format("{:.2f}")

# Save Excel file (your existing code)
output_file = "price_comparison.xlsx"
styled.to_excel(output_file, engine="openpyxl")

# --- NEW: Create HTML table with the same colors ---
def create_colored_html_table(df):
    """Create HTML table with conditional formatting matching Excel"""
    html_parts = []
    
    # Table header with styling
    html_parts.append('''
    <table border="1" style="border-collapse: collapse; font-family: Arial, sans-serif; margin: 20px 0;">
        <thead>
            <tr style="background-color: #f0f0f0; font-weight: bold;">
                <th style="padding: 8px; text-align: left;">Collection No</th>
    ''')
    
    for col in df.columns:
        html_parts.append(f'<th style="padding: 8px; text-align: center;">{col}</th>')
    
    html_parts.append('</tr></thead><tbody>')
    
    # Table rows with conditional formatting
    for idx, row in df.iterrows():
        html_parts.append('<tr>')
        html_parts.append(f'<td style="padding: 8px; font-weight: bold;">{idx}</td>')
        
        for col_name, value in row.items():
            if pd.isna(value):
                cell_content = "N/A"
                cell_style = "padding: 8px; text-align: center;"
            else:
                if col_name in ["Brilliant Earth %", "The Diamond Store %", "77 Diamonds %", "Diamond Heaven %"]:
                    # Apply conditional formatting
                    cell_style = f"padding: 8px; text-align: center; {get_cell_color(value)}"
                    cell_content = f"{value:.2f}%"
                else:
                    cell_style = "padding: 8px; text-align: center;"
                    cell_content = f"${value:.2f}" if "Price" in col_name else f"{value:.2f}"
            
            html_parts.append(f'<td style="{cell_style}">{cell_content}</td>')
        
        html_parts.append('</tr>')
    
    html_parts.append('</tbody></table>')
    return ''.join(html_parts)

# Create the colored HTML table
html_table = create_colored_html_table(comparison)

# Email content
subject = "Price Comparison Report"
body = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ color: #333; margin-bottom: 20px; }}
        .legend {{ 
            margin: 20px 0; 
            padding: 15px; 
            background-color: #f9f9f9; 
            border-radius: 5px; 
        }}
        .legend-item {{ margin: 5px 0; }}
        .red-sample {{ 
            display: inline-block; 
            width: 20px; 
            height: 20px; 
            background-color: #ff4444; 
            margin-right: 10px; 
            vertical-align: middle; 
        }}
        .green-sample {{ 
            display: inline-block; 
            width: 20px; 
            height: 20px; 
            background-color: #44ff44; 
            margin-right: 10px; 
            vertical-align: middle; 
        }}
    </style>
</head>
<body>
    <div class="header">
        <h2>💎 Daily Price Comparison Report</h2>
        <p>Hello,<br><br>
           Please find below the latest price comparison report comparing competitor prices against DiamondsFactory:
        </p>
    </div>
    
    <div class="legend">
        <h3>Color Legend:</h3>
        <div class="legend-item">
            <span class="red-sample"></span>
            <strong>Red:</strong> Competitor price is >5% higher than DiamondsFactory (expensive)
        </div>
        <div class="legend-item">
            <span class="green-sample"></span>
            <strong>Green:</strong> Competitor price is lower than DiamondsFactory (cheaper)
        </div>
        <div class="legend-item">
            <strong>No color:</strong> Competitor price is 0-5% higher than DiamondsFactory
        </div>
    </div>
    
    {html_table}
    
    <div style="margin-top: 30px;">
        <p><strong>Notes:</strong></p>
        <ul>
            <li>Percentages show how competitor prices compare to DiamondsFactory prices</li>
            <li>Positive percentages mean competitor is more expensive</li>
            <li>Negative percentages mean competitor is cheaper</li>
            <li>Data is based on yesterday's average prices by collection</li>
        </ul>
    </div>
    
    <p style="margin-top: 20px;"><br>Best regards,<br><strong>Price Monitoring Bot</strong> 🤖</p>
</body>
</html>
"""

# Send as HTML with colors preserved
send_email(subject, body, is_html=True)

print("✅ Email with colorful HTML table sent successfully!")
print("🎨 Colors preserved: Red for >5% difference, Green for negative differences")
print("📊 Now includes all 5 websites: DF, Brilliant Earth, The Diamond Store, 77 Diamonds, and Diamond Heaven")

in this code i have to modify like, i want to compare yesterday price with yesterday competitor price, and my base column in daimond