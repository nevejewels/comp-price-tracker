import pandas as pd
from email_service import send_email
from sqlalchemy import create_engine
import re

# Your existing database query code
engine = create_engine("postgresql+psycopg2://briqpay:briqpay111@178.79.182.27/briqpay")

query = """
SELECT
    website,
    collection_no,
    DATE(updated_date) AS price_date,
    ROUND(AVG(final_price)::numeric, 2) AS avg_final_price
FROM (
    SELECT website, collection_no, updated_date, final_price FROM price_df_scrape
    UNION ALL
    SELECT website, collection_no, updated_date, final_price FROM price_brilliantearth_scrape
    UNION ALL
    SELECT website, collection_no, updated_date, final_price FROM price_thediamondstore_scrape
    UNION ALL
    SELECT website, collection_no, updated_date, final_price FROM price_77diamonds_scrape
    UNION ALL
    SELECT website, collection_no, updated_date, final_price FROM price_diamondheaven_scrape
) AS combined
WHERE updated_date::date = CURRENT_DATE - INTERVAL '1 day'  -- Only yesterday's data
GROUP BY website, collection_no, DATE(updated_date)
ORDER BY website, collection_no, price_date;
"""

df = pd.read_sql(query, engine)
print(f"Total rows fetched: {df.shape[0]}")
print(f"Unique websites: {df['website'].unique().tolist()}")
print(f"Date being analyzed: {df['price_date'].unique()}")
df.to_excel("raw_yesterday_data.xlsx", index=False)

# Check if we have data
if df.empty:
    print("No data found for yesterday")
    exit()

# Pivot the data to get each website as a column
pivot_df = df.pivot_table(
    index="collection_no",
    columns="website",
    values="avg_final_price"
).reset_index()

print("Available columns after pivot:", pivot_df.columns.tolist())
print("Sample of pivoted data:")
print(pivot_df.head())

# Set collection_no as index for easier processing
pivot_df = pivot_df.set_index("collection_no")

# Function to calculate percentage difference compared to DiamondsFactory
def calc_pct_vs_df(competitor_col, df_col):
    """Calculate percentage difference: (competitor - df) / df * 100"""
    return ((pivot_df[df_col] - pivot_df[competitor_col]) / pivot_df[df_col]) * 100


# --- Merge competitor price and % into one column ---
def format_price_with_pct(price, pct):
    """Format competitor price with percentage difference"""
    if pd.isna(price) or pd.isna(pct):
        return "-"   # Replace N/A with "-"
    return f"{price:.2f} ({pct:.2f}%)"

comparison = pd.DataFrame({
    "DF Yesterday Price": pivot_df["diamondsfactory"],
    "Brilliant Earth Price %": [
        format_price_with_pct(price, pct) 
        for price, pct in zip(pivot_df["brilliantearth"], 
                              calc_pct_vs_df("brilliantearth", "diamondsfactory"))
    ],
    "The Diamond Store Price %": [
        format_price_with_pct(price, pct) 
        for price, pct in zip(pivot_df["thediamondstore"], 
                              calc_pct_vs_df("thediamondstore", "diamondsfactory"))
    ],
    "77 Diamonds Price %": [
        format_price_with_pct(price, pct) 
        for price, pct in zip(pivot_df["77diamonds"], 
                              calc_pct_vs_df("77diamonds", "diamondsfactory"))
    ],
    "Diamond Heaven Price %": [
        format_price_with_pct(price, pct) 
        for price, pct in zip(pivot_df["diamond-heaven"], 
                              calc_pct_vs_df("diamond-heaven", "diamondsfactory"))
    ]
}, index=pivot_df.index)

print("Sample of merged comparison data:")
print(comparison.head())


# --- Function to apply the same color logic for HTML ---
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
def extract_pct(value):
    """Extract numeric percentage from merged cell string"""
    if not isinstance(value, str):
        return None
    match = re.search(r"\((-?\d+\.?\d*)%\)", value)
    if match:
        return float(match.group(1))
    return None

def highlight(val):
    pct = extract_pct(val)
    if pct is None:
        return ""
    if pct > 5:
        return "background-color: #ff4444; color: white;"  # Red
    elif pct < -5:
        return "background-color: #44ff44; color: white;"  # Green
    return ""  # Between -5% and 5% → No color

# Only apply highlighting to percentage columns

percentage_columns = [
    "Brilliant Earth Price %",
    "The Diamond Store Price %",
    "77 Diamonds Price %",
    "Diamond Heaven Price %"
]

styled = comparison.style.map(
    highlight, subset=percentage_columns
)   


# Save Excel file
output_file = "price_comparison_yesterday.xlsx"
styled.to_excel(output_file, engine="openpyxl")

def get_cell_color_from_combined(value):
    """Return background-color CSS for merged price+% cells"""
    pct = extract_pct(value)
    if pct is None:
        return ""
    if pct > 5:
        return "background-color: #ff4444; color: white;"  # Red
    elif pct < -5:
        return "background-color: #44ff44; color: white;"  # Green
    return ""  # Between -5% and 5% → No color


# --- Create HTML table with the same colors ---
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
            if pd.isna(value) or value == "-" or value == "N/A":
                cell_content = "-"
                cell_style = "padding: 8px; text-align: center; background-color: #f5f5f5;"
            else:
                # if col_name in ["Brilliant Earth price(%)", "The Diamond Store Price (%)", "77 Diamonds Price(%)", "Diamond Heaven Price(%)"]:
                if col_name in [
                    "Brilliant Earth Price %",
                    "The Diamond Store Price %",
                    "77 Diamonds Price %",
                    "Diamond Heaven Price %"
                ]:
                    # Apply conditional formatting to combined price/percentage columns
                    cell_style = f"padding: 8px; text-align: center; {get_cell_color_from_combined(value)}"
                    cell_content = str(value)
                else:
                    # DF Yesterday Price column (already formatted)
                    cell_style = "padding: 8px; text-align: center;"
                    cell_content = str(value)
            
            html_parts.append(f'<td style="{cell_style}">{cell_content}</td>')
        
        html_parts.append('</tr>')
    
    html_parts.append('</tbody></table>')
    return ''.join(html_parts)

# Create the colored HTML table
html_table = create_colored_html_table(comparison)

# Get yesterday's date for the email
yesterday_date = df['price_date'].iloc[0].strftime('%Y-%m-%d')

# Email content
subject = f"Price Comparison Report - {yesterday_date}"
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
        <h2>💎 Daily Price Comparison Report - {yesterday_date}</h2>
        <p>Hello,<br><br>
           Please find below yesterday's price comparison report comparing competitor prices against DiamondsFactory:
        </p>
    </div>
    
    <div class="legend">
        <h3>Color Legend:</h3>
        <div class="legend-item">
            <span class="red-sample"></span>
            <strong>Red:</strong> Diamond Factory price is  (+)X% Expensive than Competitor 
        </div>
        <div class="legend-item">
            <span class="green-sample"></span>
            <strong>Green:</strong> Diamond Factory price is  (-) X% Cheaper than Competitor
        </div>
        <div class="legend-item">
            <strong>No color:</strong> Competitor price is 0-5% higher than DiamondsFactory
        </div>
    </div>
    
    {html_table}
    
    <div style="margin-top: 30px;">
        <p><strong>Notes:</strong></p>
        <ul>
            <li>All prices are from yesterday ({yesterday_date})</li>
            <li>Percentages show how competitor prices compare to DiamondsFactory prices</li>
            <li>Data is based on average prices by collection for yesterday</li>
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
print(f"📊 Yesterday's price comparison ({yesterday_date}) - All competitors vs DiamondsFactory base prices")
print(f"📈 Analyzed {len(comparison)} collections")

