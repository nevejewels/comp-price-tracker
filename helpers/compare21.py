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

# df = pd.read_sql(query, engine)
# print(f"Total rows fetched: {df.shape[0]}")
# print(f"Unique websites: {df['website'].unique().tolist()}")
# df.to_excel("report2_last2days.xlsx", index=False)

df = pd.read_excel("report2_last2days.xlsx")
# Your existing data processing code
pivot_df = df.pivot_table(
    index=["collection_no", "price_date"],
    columns="website",
    values="avg_final_price"
).reset_index()

# Get yesterday & day-before dates
unique_dates = sorted(pivot_df["price_date"].unique())
if len(unique_dates) < 2:
    raise ValueError("Not enough data for yesterday and day before yesterday")

day_before, yesterday = unique_dates

# Separate frames
y_df = pivot_df[pivot_df["price_date"] == yesterday].set_index("collection_no")
d_df = pivot_df[pivot_df["price_date"] == day_before].set_index("collection_no")

# Merge
merged = y_df.join(d_df, lsuffix="_y", rsuffix="_d", how="outer")

# Build final styled DataFrame
final = pd.DataFrame(index=merged.index)

for col in y_df.columns:  # websites
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

    final[col] = formatted

# Save
final.to_excel("report2_comparison.xlsx")
print("✅ Comparison report generated: report2_comparison.xlsx")
