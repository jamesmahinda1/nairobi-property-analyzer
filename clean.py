import pandas as pd
import numpy as np
import glob
import os

# load the most recent raw CSV
csv_path = sorted(glob.glob("data/raw/buyrentkenya_*.csv"))[-1]
df = pd.read_csv(csv_path)
print(f"Loaded {len(df)} rows from {csv_path}")

# 1. map business_function to a clean type column
function_to_type = {
    "http://purl.org/goodrelations/v1#Sell": "sale",
    "http://purl.org/goodrelations/v1#LeaseOut": "rent",
}
df["type"] = df["business_function"].map(function_to_type)

# 2. drop rows with price = 0
df = df[df["price"] > 0]
print(f"After dropping price=0: {len(df)}")

# 3. drop rows with missing bedrooms
df = df[df["bedrooms"].notna()]
print(f"After dropping NaN bedrooms: {len(df)}")

# 4. drop the 85M rent (a sale price miscategorised)
df = df[~((df["type"] == "rent") & (df["price"] > 5_000_000))]
print(f"After dropping rent price outliers: {len(df)}")

# 5. drop the 780K sale (impossibly cheap 5-bed villa)
df = df[~((df["type"] == "sale") & (df["price"] < 1_000_000))]
print(f"After dropping sale price outliers: {len(df)}")

# 6 + 7. fix implausible size_m2 values
is_house = df["category"].str.contains("houses")
is_apartment = df["category"].str.contains("flats-apartments")

tiny = (is_house & (df["size_m2"] < 60)) | (is_apartment & (df["size_m2"] < 25))
huge = (is_house & (df["size_m2"] > 3000)) | (is_apartment & (df["size_m2"] > 500))
df.loc[tiny | huge, "size_m2"] = np.nan
print(f"size_m2 with valid values after cleaning: {df['size_m2'].notna().sum()}")

# 8. confirm currency is always KES, then drop it
assert (df["currency"] == "KES").all(), "found a non-KES currency"
df = df.drop(columns=["currency"])

# 9. convert date_published to a datetime
df["date_published"] = pd.to_datetime(df["date_published"])

# 10. strip whitespace from text fields
for col in ["neighborhood", "region", "title"]:
    df[col] = df[col].str.strip()

# 11. extract listing_id from the URL (trailing number)
df["listing_id"] = df["url"].str.extract(r"-(\d+)$").astype(int)

# 12. extract property_subtype from URL slug (between -bedroom- and -for-)
df["property_subtype"] = df["url"].str.extract(r"-bedroom-([a-z]+)-for-")

# 13. extract furnished/serviced flag from title (boolean)
df["furnished"] = df["title"].str.contains(r"furnished|serviced", case=False, regex=True, na=False)
print(f"Furnished or serviced: {df['furnished'].sum()}")

# drop the now-redundant business_function column
df = df.drop(columns=["business_function"])

# save the cleaned CSV
os.makedirs("data/processed", exist_ok=True)
output_path = "data/processed/listings_clean.csv"
df.to_csv(output_path, index=False)
print(f"Saved {len(df)} cleaned rows to {output_path}")
