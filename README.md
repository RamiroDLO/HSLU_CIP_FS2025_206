# AutoCommodity Insights

A lightweight toolkit to scrape Swiss used car(Autoscout24.ch) listings, pull commodity market api data, and explore how raw material prices influence the second-hand vehicle market for our fictional client AutoHelvetia AG.

## Highlights
- **Web scraping**: Selenium-based scraper for AutoScout24.ch listings.
- **Market data**: Yahoo Finance integration for commodity price histories.
- **Analysis scripts**: Research question notebooks covering pricing, volatility, and correlations.
- **Clean datasets**: Reusable CSV outputs for downstream analytics.

## Project Structure
```
project_scraping_CIP_analysis_car_commodity_price/
├── Analysis/                # Analysis notebooks and scripts
│   ├── RQ1/                 # Research Question 1 script & analysis
│   ├── RQ2/                 # Research Question 2 script & analysis
│   └── RQ3/                 # Research Question 3 script & analysis
├── Data/                    # Data storage
│   ├── API_data_pull/       # API-fetched commodity data & script
│   ├── clean_data/          # Processed and cleaned datasets & script
│   └── Scraping/            # Web scraped data and scripts & scraper script
├── Documentation.pdf        # This documentation file
├── README.md                # Project overview
├── AI_Disclosure.md         # Gen AI usage disclosure and guidelines
├── requirements.txt         # Project dependencies
└── .gitignore               # Git ignore file


## Getting Started
1. Install dependencies listed in `requirements.txt`.
2. Use the scripts in `Data/` to fetch fresh listings and update commodity series.
3. Run the analyses under `Analysis/` to reproduce figures and insights.

## Documentation
See `Documentation.rmd` for the full project narrative, feasibility notes, and methodology details.

## Contributions
Dongyuan Gao: Scraping, Data Processing, Analysis
Cyriel Van Helleputte: Debugging for Scraper, Analysis, Git Organization
Ramiro Diez-Liebana: API Integration, Data Processing, Analysis
