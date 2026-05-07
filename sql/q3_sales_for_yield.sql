-- Q3a: Sale prices for apartments (used in yield calc).
-- Apartments only — they dominate the rental market, so yield calculations
-- are most reliable when both sides of the ratio are apartments.

SELECT
    neighborhood,
    bedrooms,
    price
FROM listings
WHERE type = 'sale'
  AND property_subtype = 'apartment';
