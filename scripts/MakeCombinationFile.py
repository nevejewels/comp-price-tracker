import pandas as pd
from itertools import product

website_name = ["diamondsfactory"]
product_url = ["https://www.brilliantearth.com/en-gb/1.4mm-Provence-Solitaire-Ring-Gold-BE1776-4345169/"]
category = ["Engaggement Ring"]
subcategory = ["Solitaire"]
collectionno = [""]
variantno = [""]
metals = ["18K White Gold", "18K Yellow Gold", "Platinum"]
stone_types = ["Natural", "Lab Grown"]
stone_shapes = ["Round", "Oval", "Emerald", "Cushion", "Radiant", "Princess", "Asscher"]
stone_carats = [0.50, 1.00, 1.50, 2.00]
colors = ["F", "G", "H", "I"]
clarities = ["VVS1"]
cuts = ["Ideal"]

# Generate all combinations
all_combinations = list(product(
    website_name,
    product_url,
    category,
    subcategory,
    collectionno,
    variantno,
    metals,
    stone_types,
    stone_shapes,
    stone_carats,
    colors,
    clarities,
    cuts
))

# Convert to DataFrame
df = pd.DataFrame(all_combinations, columns=[
    "Website", "Product URL", "Category", "Sub Category", "Collection No", "Variant No",
    "Metal", "Stone Type", "Stone Shape", "Stone Carat", "Color", "Clarity", "Cut"
])

# Output to Excel
df.to_excel(r"D:\price_scraping\files\diamond_combinations.xlsx", index=False)

print(f"✅ Generated {len(df)} combinations and saved to 'diamond_combinations.xlsx'")
