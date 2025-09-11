import pandas as pd
from sqlalchemy import create_engine

# --- Step 1: Connect with SQLAlchemy (clean way) ---
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
) AS combined
WHERE updated_date::date IN (
    CURRENT_DATE - INTERVAL '1 day',
    CURRENT_DATE - INTERVAL '2 day'
)
GROUP BY website, collection_no, DATE(updated_date)
ORDER BY website, collection_no, price_date;
"""

df = pd.read_sql(query, engine)
print(df.shape)

# --- Step 2: Pivot ---
pivot_df = df.pivot_table(
    index=["collection_no", "price_date"],
    columns="website",
    values="avg_final_price"
).reset_index()

# --- Step 3: Yesterday & day-before ---
unique_dates = sorted(df["price_date"].unique())
if len(unique_dates) < 2:
    print("Not enough dates in query result")
    exit()

day_before, yesterday = unique_dates  # [older, newer]

y_df = pivot_df[pivot_df["price_date"] == yesterday].set_index("collection_no")
d_df = pivot_df[pivot_df["price_date"] == day_before].set_index("collection_no")

# --- Step 4: Merge ---
merged = y_df.join(d_df, lsuffix="_yesterday", rsuffix="_daybefore", how="outer")

# --- Step 5: % comparison vs DiamondsFactory ---
def calc_pct(col, base_col):
    return ((merged[col] - merged[base_col]) / merged[base_col]) * 100

comparison = pd.DataFrame({
    "DF Avg Price": merged["diamondsfactory_yesterday"],
    "Brilliant Earth %": calc_pct("brilliantearth_yesterday", "diamondsfactory_yesterday"),
    "The Diamond Store %": calc_pct("thediamondstore_yesterday", "diamondsfactory_yesterday"),
}, index=merged.index)

comparison = comparison.round(2)

# --- Step 6: Styling with background colors ---
def highlight(val):
    if pd.isna(val):
        return ""
    if val > 5:
        return "background-color: red; color: white;"
    elif val < 0:
        return "background-color: green; color: white;"
    return ""

styled = comparison.style.map(
    highlight, subset=["Brilliant Earth %", "The Diamond Store %"]
).format("{:.2f}")

# --- Step 7: Export to Excel with formatting ---
output_file = "price_comparison.xlsx"
styled.to_excel(output_file, engine="openpyxl")

print(f"✅ Comparison exported to {output_file}")
