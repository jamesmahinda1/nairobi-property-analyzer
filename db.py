import pandas as pd
import sqlite3

# load the cleaned CSV
df = pd.read_csv("data/processed/listings_clean.csv")
print(f"Loaded {len(df)} rows from cleaned CSV")

# convert furnished from True/False to 0/1 to match the CHECK constraint
df["furnished"] = df["furnished"].astype(bool).astype(int)

# connect to the database (creates the file if missing)
conn = sqlite3.connect("data/property.db")

# build the schema (drops + recreates table; idempotent)
with open("sql/schema.sql") as f:
    conn.executescript(f.read())
print("Schema built from sql/schema.sql")

# insert all the rows into the listings table
df.to_sql("listings", conn, if_exists="append", index=False)

# verify by counting
count = conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0]
print(f"Inserted {count} rows into listings")

# verify the indexes exist
indexes = conn.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
print(f"Indexes: {[i[0] for i in indexes]}")

# verify NULLs were preserved
null_sizes = conn.execute("SELECT COUNT(*) FROM listings WHERE size_m2 IS NULL").fetchone()[0]
print(f"NULL size_m2 values: {null_sizes}")

conn.close()
print("Done.")
