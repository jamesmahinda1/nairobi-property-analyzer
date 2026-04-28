import requests
from bs4 import BeautifulSoup
import json
import re
import csv
import time
from datetime import datetime

USER_AGENT = "ZinduaCapstone/0.1 (student-research)"
DELAY_SECONDS = 2.5
MAX_PAGES = 10

CATEGORIES = [
    "houses-for-sale/nairobi",
    "houses-for-rent/nairobi",
    "flats-apartments-for-sale/nairobi",
    "flats-apartments-for-rent/nairobi",
]


def get_page(url):
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    time.sleep(DELAY_SECONDS)
    return response


def get_listing_urls(category, max_pages):
    urls = []
    for page in range(1, max_pages + 1):
        if page == 1:
            page_url = f"https://www.buyrentkenya.com/{category}"
        else:
            page_url = f"https://www.buyrentkenya.com/{category}?page={page}"
        print(f"  page {page}: {page_url}")
        response = get_page(page_url)
        if response.status_code != 200:
            print(f"  status {response.status_code}, stopping")
            break
        found = re.findall(r'href="(/listings/[^"]+)"', response.text)
        for path in found:
            if path not in urls:
                urls.append(path)
    return urls


def parse_listing(html):
    soup = BeautifulSoup(html, "html.parser")
    block = soup.find("script", type="application/ld+json")
    if block is None or block.string is None:
        return None
    data = json.loads(block.string)
    graph = data.get("@graph", [])

    accommodation = None
    offer = None
    address = None
    listing = None
    for entry in graph:
        kind = entry.get("@type")
        if kind == "Accommodation":
            accommodation = entry
        elif kind == "Offer":
            offer = entry
        elif kind == "PostalAddress" and "listing-" in entry.get("@id", ""):
            address = entry
        elif kind == "RealEstateListing":
            listing = entry

    if accommodation is None or offer is None or listing is None:
        return None

    size_match = re.search(r"(\d[\d,]*)\s*m²", html)
    size_m2 = int(size_match.group(1).replace(",", "")) if size_match else None

    price_spec = offer.get("priceSpecification", {})
    return {
        "url": offer.get("url"),
        "title": listing.get("name"),
        "neighborhood": address.get("addressLocality") if address else None,
        "region": address.get("addressRegion") if address else None,
        "bedrooms": accommodation.get("numberOfBedrooms"),
        "bathrooms": accommodation.get("numberOfBathroomsTotal"),
        "size_m2": size_m2,
        "price": price_spec.get("price"),
        "currency": price_spec.get("priceCurrency"),
        "business_function": offer.get("businessFunction"),
        "date_published": listing.get("datePublished"),
    }


def main():
    rows = []
    for category in CATEGORIES:
        print(f"\nCategory: {category}")
        urls = get_listing_urls(category, MAX_PAGES)
        print(f"Total listings found in {category}: {len(urls)}")
        for i, path in enumerate(urls, 1):
            full_url = "https://www.buyrentkenya.com" + path
            print(f"  {i}/{len(urls)}: {path}")
            response = get_page(full_url)
            if response.status_code != 200:
                continue
            row = parse_listing(response.text)
            if row is not None:
                row["category"] = category
                rows.append(row)

    if not rows:
        print("No listings collected.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"data/raw/buyrentkenya_{timestamp}.csv"
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved {len(rows)} listings to {output_path}")


if __name__ == "__main__":
    main()
