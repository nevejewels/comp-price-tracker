import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine
import re
from email_service import send_email
import os
from dotenv import load_dotenv
load_dotenv()
EMAIL_CONFIG = {
    'sender': os.getenv('EMAIL_SENDER'),
    'password': os.getenv('EMAIL_PASSWORD'),
    'recipients': os.getenv('EMAIL_RECIPIENTS').split(','),
    'recipients_report': os.getenv('EMAIL_RECIPIENTS_REPORT').split(','),
    'smtp_server': os.getenv('EMAIL_SMTP_SERVER'),
    'smtp_port': int(os.getenv('EMAIL_SMTP_PORT'))
}


engine = create_engine("postgresql+psycopg2://briqpay:briqpay111@178.79.182.27/briqpay")

# ===== REPORT 1: COMPETITOR PRICE COMPARISON =====
print("🔄 Generating Report 1: Competitor Price Comparison...")

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

# Load or fetch data for Report 1
df1 = pd.read_sql(query1, engine)
print(f"Total rows fetched: {df1.shape[0]}")
# df1.to_excel("yesterday_raw_data.xlsx", index=False)

# df1 = pd.read_excel("yesterday_raw_data.xlsx")
print(f"📊 Raw data shape: {df1.shape}")
print(f"📅 Available dates in data: {pd.to_datetime(df1['updated_date_t']).dt.date.unique()[:10]}")

# Process Report 1 data
df1["updated_date_t"] = pd.to_datetime(df1["updated_date_t"]).dt.date
yesterday = (datetime.now() - timedelta(days=1)).date()
print(f"🎯 Looking for yesterday date: {yesterday}")

df1_yesterday = df1[df1["updated_date_t"] == yesterday]
print(f"📈 Yesterday's data shape: {df1_yesterday.shape}")

# If no data for yesterday, use the most recent date
if df1_yesterday.empty:
    latest_date = df1["updated_date_t"].max()
    print(f"⚠️ No data for {yesterday}, using latest available date: {latest_date}")
    df1_yesterday = df1[df1["updated_date_t"] == latest_date]
    yesterday = latest_date
    print(f"📈 Latest date data shape: {df1_yesterday.shape}")

# Process Report 1 data only if we have data
if not df1_yesterday.empty:
    print("✅ Processing Report 1 with available data...")
    
    # Group and calculate averages
    df1_avg = (
        df1_yesterday.groupby(["collection_no", "competition_comparison"], as_index=False)
        .agg(
            df_final_website_price=("df_final_website_price", "mean"),
            competitor_final_price=("competitor_final_price", "mean")
        )
    )
    
    print(f"📊 Grouped data shape: {df1_avg.shape}")
    print(f"🏢 Competition types found: {df1_avg['competition_comparison'].unique()}")
    
    if not df1_avg.empty:
        # Calculate price difference percentage
        df1_avg["price_difference_pct"] = (
            (df1_avg["df_final_website_price"] - df1_avg["competitor_final_price"])
            / df1_avg["df_final_website_price"]
        ) * 100
        df1_avg["price_difference_pct"] = df1_avg["price_difference_pct"].round(2)

        # Create display text "price (xx.xx%)"
        df1_avg["comp_price_with_pct"] = (
            df1_avg["competitor_final_price"].round(2).astype(str)
            + " (" + df1_avg["price_difference_pct"].astype(str) + "%)"
        )

        # Pivot table to wide format
        pivot_df1 = df1_avg.pivot(
            index="collection_no",
            columns="competition_comparison",
            values="comp_price_with_pct"
        ).reset_index()
        
        print(f"📋 Pivot table shape: {pivot_df1.shape}")
        print(f"📋 Pivot columns: {pivot_df1.columns.tolist()}")

        # Add DF Yesterday Price column
        df1_factory = (
            df1_avg.groupby("collection_no")["df_final_website_price"].mean().round(2)
            .reset_index()
            .rename(columns={"df_final_website_price": "DF Yesterday Price"})
        )

        final_df1 = pd.merge(df1_factory, pivot_df1, on="collection_no", how="left")

        # Rename columns for clarity
        final_df1 = final_df1.rename(columns={
            "df_vs_brilliantearth": "Brilliant Earth Price %",
            "df_vs_thediamondstore": "The Diamond Store Price %",
            "df_vs_seventy_seven": "77 Diamonds Price %",
            "df_vs_diamondheaven": "Diamond Heaven Price %"
        })

        # Replace NaN with "-"
        final_df1 = final_df1.fillna("-")
        final_df1 = final_df1.set_index("collection_no")
        
        print(f"✅ Final Report 1 shape: {final_df1.shape}")
        print(f"📋 Final columns: {final_df1.columns.tolist()}")
        print("📊 Sample data:")
        print(final_df1.head())
        print("✅ Report 1 processed successfully")
    else:
        print("❌ No grouped data available for Report 1")
        final_df1 = pd.DataFrame()
else:
    print("❌ No data available for Report 1")
    final_df1 = pd.DataFrame()

# ===== REPORT 2: PRICE TREND ANALYSIS =====
print("\n🔄 Generating Report 2: Price Trend Analysis...")

query2 = """
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

# Load or fetch data for Report 2

print("📊 Fetching Report 2 data from database...")
df2 = pd.read_sql(query2, engine)
print(f"Total rows fetched: {df2.shape[0]}")
# df2.to_excel("report2_last2days.xlsx", index=False)

# df2 = pd.read_excel("report2_last2days.xlsx")
# print("📁 Loaded Report 2 data from Excel file")

# Process Report 2 data
if not df2.empty:
    pivot_df2 = df2.pivot_table(
        index=["collection_no", "price_date"],
        columns="website",
        values="avg_final_price"
    ).reset_index()

    # Get yesterday & day-before dates
    unique_dates = sorted(pivot_df2["price_date"].unique())
    if len(unique_dates) < 2:
        print("⚠️ Warning: Not enough data for Report 2 trend analysis")
        final_df2 = pd.DataFrame()
    else:
        day_before, yesterday_date = unique_dates

        # Separate frames
        y_df = pivot_df2[pivot_df2["price_date"] == yesterday_date].set_index("collection_no")
        d_df = pivot_df2[pivot_df2["price_date"] == day_before].set_index("collection_no")

        # Merge
        merged = y_df.join(d_df, lsuffix="_y", rsuffix="_d", how="outer")

        # Build final styled DataFrame
        final_df2 = pd.DataFrame(index=merged.index)

        for col in y_df.columns:  # websites
            if col == "price_date":
                continue
                
            yesterday_col = f"{col}_y"
            daybefore_col = f"{col}_d"

            # Ensure numeric (but keep NaN if missing)
            y_val = pd.to_numeric(merged[yesterday_col], errors="coerce")
            d_val = pd.to_numeric(merged[daybefore_col], errors="coerce")

            # % change
            pct_change = ((y_val - d_val) / d_val * 100).round(0)

            # Arrow logic
            arrows = pct_change.apply(lambda x: "↑" if x > 0 else ("↓" if x < 0 else "→"))

            # Format yesterday value + %change
            formatted = []
            for y, arrow, pct in zip(y_val, arrows, pct_change):
                if pd.isna(y):  # no yesterday value → show "-"
                    formatted.append("-")
                else:
                    formatted.append(f"{int(y)} ({arrow}{int(pct)}%)")

            final_df2[col] = formatted

        print("✅ Report 2 processed successfully")
else:
    print("❌ No data available for Report 2")
    final_df2 = pd.DataFrame()

# ===== HTML TABLE GENERATION FUNCTIONS =====

def extract_pct(value):
    """Extract numeric percentage from '123.45 (-5.67%)' strings"""
    if not isinstance(value, str):
        return None
    match = re.search(r"\((-?\d+\.?\d*)%\)", value)
    if match:
        return float(match.group(1))
    return None

def get_cell_color_from_combined(value):
    """Return background-color CSS for merged price+% cells"""
    pct = extract_pct(value)
    if pct is None:
        return ""
    if pct > 5:
        return "background-color: #ff4444; color: white;"  # Red (> 5%)
    elif pct < -5:
        return "background-color: #44ff44; color: black;"  # Green (< -5%)
    return ""  # Between -5% and 5% → No color

def get_trend_color(value):
    """Return background-color CSS for trend cells (Report 2) based on % change"""
    if not isinstance(value, str) or value == "-" or "(" not in value:
        return ""  # No color for missing data or invalid format
    
    # Extract numeric percentage
    match = re.search(r"\((?:↑|↓|→)?([-+]?\d+)%\)", value)
    if match:
        pct = int(match.group(1))
        if -5 <= pct <= 5:
            return ""  # No color
        elif pct > 5:
            return "background-color: #c438e0; color: white;"  # Green
        else:  # pct < -5
            return "background-color: #c438e0; color: white;"  # Red
    return ""

def create_colored_html_table(df, title, report_type="report1"):
    """Create HTML table with appropriate coloring based on report type"""
    if df.empty:
        return f'''
        <div style="margin: 30px 0;">
            <h3 style="color: #333; border-bottom: 2px solid #007acc; padding-bottom: 10px;">{title}</h3>
            <div style="padding: 20px; background-color: #fff3cd; border: 1px solid #ffeeba; border-radius: 5px;">
                <p style="color: #856404; margin: 0;">⚠️ No data available for this report.</p>
                <p style="color: #856404; margin: 5px 0 0 0; font-size: 14px;">
                    Please check if data exists for the requested date range.
                </p>
            </div>
        </div>
        '''
    
    html_parts = []
    html_parts.append(f'''
    <div style="margin: 30px 0;">
        <h3 style="color: #333; border-bottom: 2px solid #007acc; padding-bottom: 10px;">{title}</h3>
        <table border="1" style="border-collapse: collapse; font-family: Arial, sans-serif; width: 100%; margin: 10px 0;">
            <thead>
                <tr style="background-color: #007acc; color: white; font-weight: bold;">
                    <th style="padding: 10px; text-align: left;">Collection No</th>
    ''')
    
    for col in df.columns:
        html_parts.append(f'<th style="padding: 10px; text-align: center;">{col}</th>')
    html_parts.append('</tr></thead><tbody>')
    
    for idx, row in df.iterrows():
        html_parts.append('<tr>')
        html_parts.append(f'<td style="padding: 10px; font-weight: bold; background-color: #f8f9fa;">{idx}</td>')
        
        for col_name, value in row.items():
            if pd.isna(value) or value == "-":
                cell_content = "-"
                cell_style = "padding: 10px; text-align: center; background-color: #f5f5f5;"
            else:
                cell_content = str(value)
                if report_type == "report1":
                    # Report 1: Competitor comparison coloring
                    if col_name in [
                        "Brilliant Earth Price %",
                        "The Diamond Store Price %", 
                        "77 Diamonds Price %",
                        "Diamond Heaven Price %"
                    ]:
                        cell_style = f"padding: 10px; text-align: center; {get_cell_color_from_combined(value)}"
                    else:
                        cell_style = "padding: 10px; text-align: center; background-color: #f8f9fa;"
                else:
                    # Report 2: Trend coloring
                    cell_style = f"padding: 10px; text-align: center; {get_trend_color(value)}"
            
            html_parts.append(f'<td style="{cell_style}">{cell_content}</td>')
        
        html_parts.append('</tr>')
    html_parts.append('</tbody></table></div>')
    return ''.join(html_parts)

# ===== CREATE EMAIL CONTENT =====

# Generate HTML tables
html_table1 = create_colored_html_table(final_df1, "📊 Collection-wise Price Difference vs Competitors (% Δ)", "report1")
html_table2 = create_colored_html_table(final_df2, "📈 Collection-wise Price Fluctuation (Yesterday vs Previous Day Avg)", "report2")

# # Save Report 1
# with open("report1.html", "w", encoding="utf-8") as f:
#     f.write(f"""
#     <html>
#     <head>
#         <meta charset="UTF-8">
#         <title>Report 1</title>
#         <style>
#             body {{ font-family: Arial, sans-serif; margin: 20px; }}
#         </style>
#     </head>
#     <body>
#         {html_table1}
#     </body>
#     </html>
#     """)

# # Save Report 2
# with open("report2.html", "w", encoding="utf-8") as f:
#     f.write(f"""
#     <html>
#     <head>
#         <meta charset="UTF-8">
#         <title>Report 2</title>
#         <style>
#             body {{ font-family: Arial, sans-serif; margin: 20px; }}
#         </style>
#     </head>
#     <body>
#         {html_table2}
#     </body>
#     </html>
#     """)

# print("✅ Reports saved as report1.html and report2.html. Open them in your browser.")

# Yesterday date for subject
yesterday_date = (datetime.now() - pd.Timedelta(days=1)).strftime('%Y-%m-%d')

# Email content
subject = f"📊 Daily Price Reports - {yesterday_date}"
body = f"""
<html>
<head>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 20px; 
            background-color: #f8f9fa;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #007acc, #005fa3);
            color: white;
            border-radius: 10px;
        }}
        .legend {{ 
            margin: 20px 0; 
            padding: 20px; 
            background-color: #f1f3f4; 
            border-radius: 8px;
            border-left: 4px solid #007acc;
        }}
        .legend-item {{ 
            margin: 8px 0; 
            display: flex;
            align-items: center;
        }}
        .color-sample {{ 
            display: inline-block; 
            width: 25px; 
            height: 20px; 
            margin-right: 15px; 
            border-radius: 3px;
            border: 1px solid #ccc;
        }}
        .red-sample {{ background-color: #ff4444; }}
        .green-sample {{ background-color: #44ff44; }}
        .light-red-sample {{ background-color: #ff4444; }}
        .light-green-sample {{ background-color: #44ff44; }}
        .notes {{
            background-color: #e8f4f8;
            padding: 20px;
            border-radius: 8px;
            margin-top: 30px;
            border-left: 4px solid #17a2b8;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
            color: #6c757d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💎 Daily Price Monitoring Reports</h1>
            <h2>{yesterday_date}</h2>
        </div>
        
        <p style="font-size: 16px; line-height: 1.6;">
            Hello,<br><br>
            Please find below today's comprehensive price monitoring reports comparing DiamondsFactory against competitors and tracking price trends:
        </p>

        <!-- Report 1 Legend -->
        <div class="legend">
            <h3 style="margin-top: 0; color: #007acc;">🎨 Report 1 - Competitor Comparison</h3>
            <div class="legend-item">
                <span class="color-sample red-sample"></span>
                <span><strong>Red:</strong> DiamondsFactory is >5% more expensive than competitor</span>
            </div>
            <div class="legend-item">
                <span class="color-sample green-sample"></span>
                <span><strong>Green:</strong> DiamondsFactory is >5% cheaper than competitor</span>
            </div>
            <div class="legend-item">
                <span style="margin-right: 40px;"></span>
                <span><strong>No color:</strong> Price difference within ±5%</span>
            </div>
        </div>

        {html_table1}

        <!-- Report 2 Legend -->
        <div class="legend">
            <h3 style="margin-top: 0; color: #007acc;">📈 Report 2 - Price Trends</h3>
            <div class="legend-item">
                <span class="color-sample" style="background-color: #c438e0; display: inline-block; width: 15px; height: 15px; margin-right: 8px; border-radius: 3px;"></span>
                <span><strong>Purple:</strong> Price change greater than ±5% compared to previous day</span>
            </div>
            <div class="legend-item">
                <span style="margin-right: 40px;"></span>
                <span><strong>No color:</strong> Price change between -5% and +5%</span>
            </div>
        </div>

        {html_table2}

        <div class="notes">
            <h3 style="margin-top: 0; color: #17a2b8;">📋 Important Notes</h3>
            <ul style="line-height: 1.8;">
                <li><strong>Data Date:</strong> All prices are from {yesterday_date}</li>
                <li><strong>Report 1:</strong> Shows competitor prices vs DiamondsFactory with percentage differences</li>
                <li><strong>Report 2:</strong> Shows price trends with arrows indicating direction of change</li>
                <li><strong>Calculations:</strong> Based on average prices by collection for the respective dates</li>
                <li><strong>Missing Data:</strong> "-" indicates no data available for that combination</li>
            </ul>
        </div>
        
        <div class="footer">
            <p><strong>Best regards,<br>Price Monitoring System 🤖</strong></p>
            <p style="font-size: 12px; margin-top: 10px;">
                This is an automated report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        </div>
    </div>
</body>
</html>
"""



# Save processed data
if not final_df1.empty:
    # final_df1.to_excel("yesterday_price_comparison.xlsx")
    print("💾 Saved Report 1 to yesterday_price_comparison.xlsx")
else:
    print("⚠️ Report 1 empty - no Excel file saved")
    
if not final_df2.empty:
    # final_df2.to_excel("report2_comparison.xlsx")
    print("💾 Saved Report 2 to report2_comparison.xlsx")
else:
    print("⚠️ Report 2 empty - no Excel file saved")

# Send email
print("📧 Sending combined email report...")
# send_email(subject, body, is_html=True) 
send_email(subject, body, recipients=EMAIL_CONFIG['recipients_report'], is_html=True)

print("✅ Combined email sent successfully with both reports!")
print("📊 Report 1: Competitor price comparison")
print("📈 Report 2: Price trend analysis")
print(f"📅 Date analyzed: {yesterday_date}")