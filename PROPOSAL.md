# Nairobi Property Market Analyzer

**Capstone Project — Zindua School**
**By:** James Mahinda

---

## Project Overview

An interactive web dashboard that analyzes the Nairobi property market — pulling live listings from property websites, cleaning and structuring them, and turning them into clear visuals that show how prices, sizes, and rental yields vary across the city's neighborhoods.

## Problem Statement

Property listings in Nairobi are scattered across multiple websites with no easy way to compare neighborhoods side by side. A buyer, renter, or curious analyst can't quickly answer questions like *"how does Kileleshwa compare to Lavington on price per square meter?"* or *"which neighborhoods offer the best rental yields?"* Existing portals show individual listings but never the patterns across them. This project turns scattered listings into clear, explorable insights.

## Research Questions

1. How do property prices vary across Nairobi's main neighborhoods?
2. Which neighborhoods are priced at a premium, and which offer better value?
3. Which neighborhoods give the highest estimated rental yields?
4. How much do property type, size, and bedroom count affect price?
5. What do these patterns look like geographically on a map of Nairobi?

## Data Sources

- **Property listings** scraped from BuyRentKenya (the primary Kenyan property portal used for this project)
- **Nairobi sub-county boundaries** from KNBS / open geographic data, used for the map layer

## What I'm Doing — Process

The project follows the full data analysis pipeline taught across the course:

**1. Collecting the data.** Build a Python web scraper that pulls property listings from the chosen sites — capturing price, location, property type, number of bedrooms, size, and any other useful attributes.

**2. Cleaning the data.** Real listings are messy: prices appear in different formats, neighborhoods are spelled inconsistently, some entries are duplicates. I'll standardize all of this using Pandas so everything is comparable.

**3. Storing the data.** Load the cleaned dataset into a SQLite database with a proper schema. This makes the data queryable using SQL — one of the core skills covered in the course.

**4. Analyzing the data.** Use SQL queries and Pandas to calculate summary statistics for each neighborhood — average price, price per square meter, distribution of property types, and estimated rental yields.

**5. Mapping the data.** Use GeoPandas to join the listings with Nairobi's sub-county map, so prices and yields can be shown geographically as a colored map of the city.

**6. Building the dashboard.** Wrap all of this into a Streamlit web app with multiple tabs — so anyone can explore the findings interactively, filter by neighborhood, and compare property types.

## Tools

Python, Pandas, NumPy, SQLite, Matplotlib, Plotly, GeoPandas, Streamlit, Git/GitHub.

## Final Dashboard

The deliverable is a Streamlit app with the following tabs:

- **Overview** — headline numbers and a summary of what the data shows.
- **Map View** — interactive map of Nairobi colored by price per m² or estimated rental yield.
- **Price Analysis** — distributions, comparisons, and rankings by neighborhood and property type.
- **Best Value** — neighborhoods that combine reasonable prices with strong estimated yields.

## Author

James Mahinda — Zindua School (2026)
