-- Q3b: Unfurnished rent prices for apartments (used in yield calc).
-- Furnished/serviced rentals carry a 30-80% premium, so we exclude them
-- to get a fair like-for-like comparison with sale prices.

SELECT
    neighborhood,
    bedrooms,
    price
FROM listings
WHERE type = 'rent'
  AND property_subtype = 'apartment'
  AND furnished = 0;
