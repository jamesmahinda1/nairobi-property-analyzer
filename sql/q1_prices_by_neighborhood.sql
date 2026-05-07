-- Q1: Prices by neighborhood
-- Pulls every listing with its neighborhood, type, and price.
-- The notebook computes medians and rankings in Pandas.

SELECT
    neighborhood,
    type,
    price
FROM listings
WHERE price > 0;
