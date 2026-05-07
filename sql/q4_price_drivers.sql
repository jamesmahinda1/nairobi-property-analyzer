-- Q4: Price drivers — how price varies with bedrooms within each neighborhood.
-- HAVING n >= 3 keeps only (neighborhood, bedrooms) combinations
-- with enough listings to be meaningful.

SELECT
    neighborhood,
    bedrooms,
    COUNT(*) AS n,
    ROUND(AVG(price), 0) AS avg_price
FROM listings
WHERE type = 'sale'
GROUP BY neighborhood, bedrooms
HAVING n >= 3
ORDER BY neighborhood, bedrooms;
