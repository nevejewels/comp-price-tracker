import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine
import re
from email_service import send_email

engine = create_engine("postgresql+psycopg2://briqpay:briqpay111@178.79.182.27/briqpay")

query1 = """
select 
    a.collection_no,
    a.category,
    a.sub_category,
    a.metal_t,
    a.stone_type_t,
    a.updated_date_t,
    a.promotion_price_e as df_final_website_price,
    b.final_price_e as competitor_final_price,
    'df_vs_diamondheaven' as competition_comparison
from public.price_df_scrape a
join price_diamondheaven_scrape b
  on a.metal_t = b.metal_t
 and a.stone_type_t = b.stone_type_t
 and a.category = b.category
 and a.collection_no = b.collection_no
 and a.updated_date_t = b.updated_date_t
 and a.sub_category = b.sub_category
where a.updated_date_t >= '2025-08-20'

union all

select 
    a.collection_no,
    a.category,
    a.sub_category,
    a.metal_t,
    a.stone_type_t,
    a.updated_date_t,
    a.promotion_price_e as df_final_website_price,
    b.final_price_e as competitor_final_price,
    'df_vs_thediamondstore' as competition_comparison
from public.price_df_scrape a
join price_thediamondstore_scrape b
  on a.metal_t = b.metal_t
 and a.stone_type_t = b.stone_type_t
 and a.category = b.category
 and a.collection_no = b.collection_no
 and a.updated_date_t = b.updated_date_t
 and a.sub_category = b.sub_category
where a.updated_date_t >= '2025-08-19'

union all

select 
    a.collection_no,
    a.category,
    a.sub_category,
    a.metal_t,
    a.stone_type_t,
    a.updated_date_t,
    a.promotion_price_e as df_final_website_price,
    b.final_price_e as competitor_final_price,
    'df_vs_brilliantearth' as competition_comparison
from public.price_df_scrape a
join public.price_brilliantearth_scrape b
  on a.metal_t = b.metal_t
 and a.stone_type_t = b.stone_type_t
 and a.stone_shape_t = b.stone_shape_t
 and a.stone_carat = b.stone_carat
 and a.clarity_t = b.clarity_t
 and a.cut_t = b.cut_t
 and a.color = b.color
 and a.category = b.category
 and a.sub_category = b.sub_category
 and a.collection_no = b.collection_no
 and a.updated_date_t = b.updated_date_t
where a.updated_date_t >= '2025-07-02'

union all

select 
    a.collection_no,
    a.category,
    a.sub_category,
    a.metal_t,
    a.stone_type_t,
    a.updated_date_t,
    a.promotion_price_e as df_final_website_price,
    b.final_price_e as competitor_final_price,
    'df_vs_seventy_seven' as competition_comparison
from public.price_df_scrape a
join public.price_77diamonds_scrape b
  on a.metal_t = b.metal_t
 and a.stone_type_t = b.stone_type_t
 and a.stone_shape_t = b.stone_shape_t
 and a.stone_carat = b.stone_carat
 and a.clarity_t = b.clarity_t
 and a.cut_t = b.cut_t
 and a.color = b.color
 and a.category = b.category
 and a.sub_category = b.sub_category
 and a.collection_no = b.collection_no
 and a.updated_date_t = b.updated_date_t
where a.updated_date_t >= '2025-07-02'
"""

# df = pd.read_sql(query1, engine)
# print(f"Total rows fetched: {df.shape[0]}")
# print(f"Date being analyzed: {df['updated_date_t'].unique()}")
# df.to_excel("yesterday_raw_data.xlsx", index=False)

df = pd.read_excel("yesterday_raw_data.xlsx")
print(df.shape)

df["updated_date_t"] = pd.to_datetime(df["updated_date_t"]).dt.date
yesterday = (datetime.now() - timedelta(days=1)).date()
df_yesterday = df[df["updated_date_t"] == yesterday]
print("Yesterday's data shape:", df_yesterday.shape)

# Step 2: group by collection_no & competition_comparison
df_avg = (
    df_yesterday.groupby(["collection_no", "competition_comparison"], as_index=False)
    .agg(
        df_final_website_price=("df_final_website_price", "mean"),
        competitor_final_price=("competitor_final_price", "mean")
    )
)

# Step 3: add percentage difference (rounded to 2 decimals)
df_avg["price_difference_pct"] = (
    (df_avg["df_final_website_price"] - df_avg["competitor_final_price"])
    / df_avg["df_final_website_price"]
) * 100
df_avg["price_difference_pct"] = df_avg["price_difference_pct"].round(2)

# Optionally save to Excel
df_avg.to_excel("yesterday_avg_prices.xlsx", index=False)


# Step 4: create display text "price (xx.xx%)"
df_avg["comp_price_with_pct"] = (
    df_avg["competitor_final_price"].round(2).astype(str)
    + " (" + df_avg["price_difference_pct"].astype(str) + "%)"
)

# Step 5: Pivot table to wide format
pivot_df = df_avg.pivot(
    index="collection_no",
    columns="competition_comparison",
    values="comp_price_with_pct"
).reset_index()

# Step 6: Add DF Yesterday Price column
df_factory = (
    df_avg.groupby("collection_no")["df_final_website_price"].mean().round(2)
    .reset_index()
    .rename(columns={"df_final_website_price": "DF Yesterday Price"})
)

final_df = pd.merge(df_factory, pivot_df, on="collection_no", how="left")

# Step 7: Rename columns for clarity
final_df = final_df.rename(columns={
    "df_vs_brilliantearth": "Brilliant Earth Price %",
    "df_vs_thediamondstore": "The Diamond Store Price %",
    "df_vs_seventy_seven": "77 Diamonds Price %",
    "df_vs_diamondheaven": "Diamond Heaven Price %"
})

# Replace "nan (nan%)" with "-"
final_df = final_df.fillna("-")

# Save result
final_df.to_excel("yesterday_price_comparison.xlsx", index=False)

print(final_df.head())




final_df = final_df.set_index("collection_no")

# --- Extract % from combined cell ---
def extract_pct(value):
    """Extract numeric percentage from '123.45 (-5.67%)' strings"""
    if not isinstance(value, str):
        return None
    match = re.search(r"\((-?\d+\.?\d*)%\)", value)
    if match:
        return float(match.group(1))
    return None

# --- Apply coloring logic ---
def get_cell_color_from_combined(value):
    """Return background-color CSS for merged price+% cells"""
    pct = extract_pct(value)
    if pct is None:
        return ""
    if pct > 5:
        return "background-color: #ff4444; color: white;"  # Red (> 5%)
    elif pct < -5:
        return "background-color: #44ff44; color: white;"  # Green (< -5%)
    return ""  # Between -5% and 5% → No color

# --- Create HTML table with colors ---
def create_colored_html_table(df):
    html_parts = []
    html_parts.append('''
    <table border="1" style="border-collapse: collapse; font-family: Arial, sans-serif; margin: 20px 0;">
        <thead>
            <tr style="background-color: #f0f0f0; font-weight: bold;">
                <th style="padding: 8px; text-align: left;">Collection No</th>
    ''')
    for col in df.columns:
        html_parts.append(f'<th style="padding: 8px; text-align: center;">{col}</th>')
    html_parts.append('</tr></thead><tbody>')
    
    for idx, row in df.iterrows():
        html_parts.append('<tr>')
        html_parts.append(f'<td style="padding: 8px; font-weight: bold;">{idx}</td>')
        
        for col_name, value in row.items():
            if pd.isna(value) or value == "-":
                cell_content = "-"
                cell_style = "padding: 8px; text-align: center; background-color: #f5f5f5;"
            else:
                if col_name in [
                    "Brilliant Earth Price %",
                    "The Diamond Store Price %",
                    "77 Diamonds Price %",
                    "Diamond Heaven Price %"
                ]:
                    cell_style = f"padding: 8px; text-align: center; {get_cell_color_from_combined(value)}"
                else:
                    cell_style = "padding: 8px; text-align: center;"
                cell_content = str(value)
            
            html_parts.append(f'<td style="{cell_style}">{cell_content}</td>')
        
        html_parts.append('</tr>')
    html_parts.append('</tbody></table>')
    return ''.join(html_parts)

# Create HTML table
html_table = create_colored_html_table(final_df)

# Yesterday date for subject
yesterday_date = (datetime.now() - pd.Timedelta(days=1)).strftime('%Y-%m-%d')

# Email content
subject = f"Price Comparison Report - {yesterday_date}"
body = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .legend {{ margin: 20px 0; padding: 15px; background-color: #f9f9f9; border-radius: 5px; }}
        .legend-item {{ margin: 5px 0; }}
        .red-sample {{ display: inline-block; width: 20px; height: 20px; background-color: #ff4444; margin-right: 10px; }}
        .green-sample {{ display: inline-block; width: 20px; height: 20px; background-color: #44ff44; margin-right: 10px; }}
    </style>
</head>
<body>
    <h2>💎 Daily Price Comparison Report - {yesterday_date}</h2>
    <p>Hello,<br><br>
       Please find below yesterday's price comparison report comparing competitor prices against DiamondsFactory:
    </p>

    <div class="legend">
        <h3>Color Legend:</h3>
        <div class="legend-item">
            <span class="red-sample"></span>
            <strong>Red:</strong> DiamondsFactory is >5% more expensive
        </div>
        <div class="legend-item">
            <span class="green-sample"></span>
            <strong>Green:</strong> DiamondsFactory is >5% cheaper
        </div>
        <div class="legend-item">
            <strong>No color:</strong> Difference within ±5%
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

    
    <p style="margin-top: 20px;">Best regards,<br><strong>Price Monitoring Bot</strong> 🤖</p>
</body>
</html>
"""

# Send email
send_email(subject, body, is_html=True)

print("✅ Email sent successfully with colorful HTML table!")




