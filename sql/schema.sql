-- Nairobi Property Market Analyzer — schema
-- Single denormalized listings table (~940 rows).

DROP TABLE IF EXISTS listings;

CREATE TABLE listings (
    listing_id        INTEGER PRIMARY KEY,
    url               TEXT NOT NULL,
    title             TEXT,
    neighborhood      TEXT NOT NULL,
    region            TEXT,
    bedrooms          INTEGER,
    bathrooms         INTEGER,
    size_m2           REAL,
    price             INTEGER NOT NULL,
    type              TEXT NOT NULL CHECK (type IN ('sale', 'rent')),
    category          TEXT NOT NULL,
    property_subtype  TEXT,
    furnished         INTEGER NOT NULL CHECK (furnished IN (0, 1)),
    date_published    TEXT
);

CREATE INDEX idx_neighborhood_type ON listings(neighborhood, type);
