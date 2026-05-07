-- Q2: Price per square meter
-- Pulls listings where size is known so we can compute price/m² in Pandas.

SELECT
    neighborhood,
    type,
    price,
    size_m2
FROM listings
WHERE size_m2 IS NOT NULL;
