# _build_geo_lookup.py — temp script. Run once.
# Output: data/processed/neighborhood_to_subcounty.csv

import pandas as pd
import geopandas as gpd
import requests
import time
from datetime import date

# Step 1: load unique neighborhoods from cleaned listings
listings = pd.read_csv("data/processed/listings_clean.csv")
neighborhoods = sorted(listings["neighborhood"].unique())
print(f"Geocoding {len(neighborhoods)} neighborhoods...")

# Step 2: geocode each via OSM Nominatim (1 req/sec rate limit)
# Some BRK-style names need a different Nominatim query.
QUERY_OVERRIDES = {
    "Westlands Area": "Westlands, Nairobi, Kenya",
    "Joska": "Joska, Machakos, Kenya",
    "Riverside": "Riverside Drive, Nairobi, Kenya",
    "Buruburu": "Buruburu Estate, Nairobi, Kenya",
}
# Manual overrides applied AFTER the spatial join.
# Dagoretti Corner geocodes to (-1.2991, 36.7588), the Ngong Road / Naivasha Road
# junction. The IEBC boundary places that point in Kibra, but common usage and the
# place name itself ("Dagoretti Corner") put it in Dagoretti South. We override.
MANUAL_OVERRIDES = {
    "Dagoretti Corner": "DagorettiSouth",
}
rows = []
for n in neighborhoods:
    query = QUERY_OVERRIDES.get(n, f"{n}, Nairobi, Kenya")
    r = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": query, "format": "json", "limit": 1},
        headers={"User-Agent": "ZinduaCapstone/0.1 (student-research)"},
        timeout=30,
    )
    data = r.json()
    if data:
        rows.append({"neighborhood": n, "lat": float(data[0]["lat"]), "lon": float(data[0]["lon"])})
        print(f"  {n}: ok")
    else:
        rows.append({"neighborhood": n, "lat": None, "lon": None})
        print(f"  {n}: NOT FOUND")
    time.sleep(1.1)

geo_df = pd.DataFrame(rows)

# Step 3: build a points GeoDataFrame from non-null coords
located = geo_df.dropna(subset=["lat", "lon"]).copy()
points = gpd.GeoDataFrame(
    located,
    geometry=gpd.points_from_xy(located["lon"], located["lat"]),
    crs="EPSG:4326",
)

# Step 4: load Nairobi sub-county polygons and spatial-join
polygons = gpd.read_file("data/geo/nairobi_sub_counties.geojson")
joined = gpd.sjoin(points, polygons, how="left", predicate="within")

# Step 5: build the lookup with provenance header
lookup = joined[["neighborhood", "sub_county", "lat", "lon"]].copy()

# apply manual overrides
for n, sc in MANUAL_OVERRIDES.items():
    lookup.loc[lookup["neighborhood"] == n, "sub_county"] = sc

lookup["in_nairobi"] = lookup["sub_county"].notna()
lookup = lookup.sort_values("neighborhood").reset_index(drop=True)

header = [
    "# Neighborhood -> sub-county lookup for Nairobi listings.",
    "# Source: (1) geocoded via OpenStreetMap Nominatim API,",
    "#         (2) spatial-joined against Nairobi sub-county polygons from GADM v4.1",
    "#             (https://gadm.org/), level 2 = constituency.",
    f"# Generated: {date.today()}",
    "",
]

out_path = "data/processed/neighborhood_to_subcounty.csv"
with open(out_path, "w", encoding="utf-8", newline="") as f:
    f.write("\n".join(header))
    lookup.to_csv(f, index=False)

print(f"\nSaved {len(lookup)} entries to {out_path}")
print(f"In Nairobi: {lookup['in_nairobi'].sum()}, outside: {(~lookup['in_nairobi']).sum()}")
