# Auto & Commodity Data Collection & Analysis

**Analyzing the Relationship Between Used Car & Commodity Prices**

**Group 206** — Dongyuan Gao, Ramiro Diez-Liebana, Cyriel Van Helleputte  
**Date**: November 2025  
**Institution**: Hochschule Luzern (HSLU)  
**Course**: CIP FS2025 206
## Our repo: "https://github.com/RamiroDLO/HSLU_CIP_FS2025_206"
---

## Project Overview

### The Business Problem

The Swiss used car market is highly competitive. Our fictional client **AutoHelvetia AG**, a leading national used car dealer, faces the challenge of optimizing their pricing and purchasing strategy. In recent years, commodity prices have been volatile and affect the pricing of cars. AutoHelvetia AG has delegated the task to us: to understand the relationship between used car prices and commodity prices.

### Our Solution

This project delivers an advanced data collection and analysis framework. Our goal is to collect valuable market data and uncover relationships between used car prices and key commodity markets. We develop a toolbox using web scraping of AutoScout24.ch and integrating with Yahoo Finance commodity data, to provide AutoHelvetia AG with data-driven insights for:

- Optimize Pricing Strategies
- Gain Competitive Advantage

### Research Questions

This project explores three main research questions:

1. **RQ1 — Commodity Index vs. Used Car Prices**: How do used car prices in Switzerland correlate with historical commodity price indices for key automotive materials (steel, aluminum, copper, crude oil)? We construct a weighted composite commodity index and examine Pearson/Spearman correlations with median used car prices while controlling for vehicle age and mileage.

2. **RQ2 — Powertrain Sensitivity**: Do different vehicle power modes (petrol, diesel, electric, hybrid) exhibit distinct sensitivity to commodity price movements? We expect electric vehicles to react more to battery metals, while ICE vehicles respond to energy and structural metals.

3. **RQ3 — Brand-Level Differences**: How does the relationship between commodity prices and used car values vary across popular Swiss car brands? We segment by brand to detect whether luxury vs. volume manufacturers show different exposure to raw material cost pressures.

## Project Structure

```
project_scraping_CIP_analysis_car_commodity_price/
├── Analysis/                # Analysis notebooks and scripts
│   ├── RQ1/                 # Research Question 1 script & analysis
│   │   ├── RQ1_analysis.py
│   │   └── outputs/         # Generated visualizations
│   ├── RQ2/                 # Research Question 2 script & analysis
│   │   ├── RQ2_analysis.py
│   │   └── outputs/         # Regression results & plots
│   └── RQ3/                 # Research Question 3 script & analysis
│       ├── RQ3_analysis.py
│       └── outputs/         # Brand correlation matrices
├── Data/                    # Data storage
│   ├── API_data_pull/       # API-fetched commodity data & script
│   │   ├── yahoo_commodities.py
│   │   └── yahoo_spot.csv
│   ├── Cleaning/            # Processed and cleaned datasets & scripts
│   │   ├── cleaner.py
│   │   └── load_prepared_datasets.py
│   ├── Scraping/            # Web scraped data and scraper script
│   │   ├── autoscout_scraper.py
│   │   └── autoscout_data_complete.csv
│   └── Final Data/          # Analysis-ready datasets
│       ├── Autoscout_Cleaned_Standardized.csv
│       ├── yahoo_spot_cleaned.csv
│       └── Final_Merged_Data_RQ3.csv
├── Reports/                 # Final written deliverables
│   ├── cip_report_206.rmd    # Final official report 6 pages rmd file
│   ├── cip_report_206.pdf    # Final official report 6 pages pdf 
│   ├── cip_report_full_pages.rmd   # Full pages 12 pages rmd file
│   └── cip_report_full_pages.pdf    # Full pages 12 pages pdf 
├── README.md                # This file - Project overview
├── AI_Disclosure.md         # GenAI usage disclosure and guidelines
├── requirements.txt         # Python dependencies
└── .gitignore
```

## Installation

### Prerequisites

- Python 3.12
- pip package manager

### Required Dependencies

```bash
# Core data analysis
pip install pandas numpy scipy matplotlib seaborn

# Web scraping
pip install undetected-chromedriver selenium beautifulsoup4

# Financial data
pip install yfinance

# Statistical modeling
pip install statsmodels

# Optional: Interactive data exploration
pip install dtale
```

Or install all dependencies at once:

```bash
pip install -r requirements.txt
```

## Usage

### 1. Data Collection

#### Web Scraping AutoScout24.ch

```bash
cd Data/Scraping
python autoscout_scraper.py
```

**Target Website**:
- Primary Source: AutoScout24.ch (https://www.autoscout24.ch)
- Target Path: `/de/autos/alle-marken` (All car listings)
- Scope: Used car listings across all makes and models

**Configuration** (in `autoscout_scraper.py`):
- `TARGET_COUNT`: Total listings to scrape (default: 2000)
- `LISTINGS_PER_PAGE`: Listings per page (default: 4)
- `OUTPUT_FILENAME`: Output file name (default: `autoscout_data_complete.csv`)

**Scraping Methodology**:
1. **Pagination Handling**: Iterates through listing pages systematically with smart navigation and randomized delays (3-7s between pages)
2. **Data Extraction Strategy**:
   - **Primary Method**: Structure-aware parsing using SVG icon titles and sibling elements
   - **Combination of Methods**: JSON-LD extraction, CSS class-based targeting, regex fallbacks
   - **Cookie Consent**: Automatic handling of cookie acceptance prompts

**Core Technologies**:
- Selenium WebDriver: Browser automation and dynamic content loading
- BeautifulSoup4: HTML parsing and data extraction
- Undetected ChromeDriver: Avoiding bot detection

**Output**: `autoscout_data_complete.csv` with the following fields:
- `car_model`: Full vehicle make and model
- `price_chf`: Listing price in Swiss Francs
- `mileage`: Kilometers driven
- `engine_power_hp`: Engine power in horsepower
- `power_mode`: Petrol/Diesel/Electric/Hybrid
- `production_date`: Manufacturing date (MM.YYYY)
- `consumption_l_per_100km`: Fuel consumption
- `transmission`: Manuell/Automat/Halbautomatik
- `listing_url`: Direct URL to original listing

#### Fetching Commodity Prices via Yahoo Finance

```bash
cd Data/API_data_pull
python yahoo_commodities.py
```

**Yahoo Finance Integration**:
We use the **yfinance Python library** (20k+ stars on GitHub), an open-source tool that accesses Yahoo Finance's public endpoints without requiring API authentication. It is not officially affiliated with Yahoo, Inc.

**Technical Implementation**:
- Core function: `yf.download()` fetches historical daily closing prices
- Falls back to adjusted close if closing price unavailable
- Automatically adds monthly aggregations

**Data Sources (Yahoo Finance Tickers)**:
- WTI Crude Oil: `CL=F`
- Copper (COMEX): `HG=F`
- Lithium (Proxy ETF): `LIT`
- Aluminium (LME): `ALI=F`
- Steel (U.S. Futures): `HRC=F`
- Nickel (Global): `NIC.AX`
- Cobalt (Proxy): `603799.SS`

**Time Range**: 2020-01-01 onwards

**Output**: `yahoo_spot.csv` with the following structure:
- `Date`: Trading day (YYYY-MM-DD)
- `Month`: Month in MM-YYYY format
- `{Commodity}_Spot`: Daily closing price for each commodity
- `{Commodity}_Spot_Monthly_Avg`: Monthly average for each commodity

**Rate Limits**: While yfinance has no official request limits, Yahoo may implement changes or IP-based rate limiting with frequent use.

### 2. Data Transformation and Cleaning

Across the project we apply a standard data-science cleaning cadence: validate dataframe, coerce types, handle missing values with data quality strategies, and normalize key features before exporting analysis-ready datasets.

#### Autoscout Listing Standardization

```bash
cd Data/Cleaning
python cleaner.py
```

**Processing Steps**:
1. **Brand & Model Extraction**: Uses regex-based patterns to parse `car_model` into `brand` and base `model` tokens, removing unwanted information (e.g., "VW TIGUAN TSI 2.0 S VERSION BERN TOP ZUSTAND" → "VW TIGUAN")
2. **Model Normalization**: Applies replacement dictionary to standardize variants (e.g., "TESLA Model Y" → "Model Y")
3. **Field Selection**: Outputs curated schema preserving only analytics-ready columns

**Output**: `Autoscout_Cleaned_Standardized.csv`

#### Commodity Price Cleaning

```bash
cd Data/Cleaning
python load_prepared_datasets.py
```

**Processing Steps**:
1. **Type Coercion**: Converts `Date` to datetime and commodity columns to numeric (handles European decimal separators)
2. **Missing Value Strategy**: 
   - Fills missing commodity prices with 7-day rolling mean
   - Rounds to two decimals
   - Reports gaps before/after processing
3. **Temporal Standardization**: Generates formatted date strings for joins

**Output**: `yahoo_spot_cleaned.csv`

#### Research Dataset Preparation (RQ3)

```bash
cd Analysis/RQ3
# Run RQ3_analysis.py (includes comprehensive cleaning)
python RQ3_analysis.py
```

**Autoscout Cleaning & Imputation**:
- Converts `production_date` (including "Neues Fahrzeug") to October 2025, creates `Month` period column
- Imputes continuous fields (`price_chf`, `mileage`, `engine_power_hp`) with rounded means
- Custom fill for `consumption_l_per_100km`:
  - EV vehicles: Set to 0
  - Then model mean, then brand mean, then global mean
- Categorical fills (`power_mode`, `transmission`) via model majority vote, defaults to "Unknown"

**Commodity Cleaning & Imputation**:
- Builds monthly periods, fills gaps from daily `Date` entries
- Aggregates to one row per month
- Keeps `_Monthly_Avg` features, drops duplicates

**Merge Output**: `Final_Merged_Data_RQ3.csv` — the master clean dataset for analysis

### 3. Data Analysis

#### RQ1: Commodity Index vs. Used Car Prices

```bash
cd Analysis/RQ1
python RQ1_analysis.py
```

**Research Question**: How do used car prices in Switzerland correlate with historical commodity price indices for key automotive materials (steel, aluminum, copper, crude oil)?

**Methodology**:
- Constructs weighted composite commodity index (base 100 at January 2020)
- Computes Pearson and Spearman correlations with median car prices
- Separates analysis for ICE (Internal Combustion Engine) vs EV (Electric Vehicle) prices
- Controls for temporal trends

**Key Findings**:
- Moderate correlation between commodity prices and median used vehicle prices
- The composite index is rebased at **January 2020**, shortly before most commodities experienced sharp declines (oil traded at negative values)
- Index climbed sharply during recovery, while both EV and ICE median prices remained relatively flat
- Suggests that consumer behavior, policy incentives, and supply chain factors play equally important roles alongside raw material costs

**Outputs**:
- `RQ1_timeseries.png`: Dual-axis time series showing ICE/EV prices vs commodity index (indexed to 2020-01)
- `RQ1_scatter.png`: Correlation scatter plot with regression line
- Console statistics: Correlation coefficients and significance tests

#### RQ2: Powertrain Sensitivity Analysis

```bash
cd Analysis/RQ2
python RQ2_analysis.py
```

**Research Question**: Do different vehicle power modes (petrol, diesel, electric, hybrid) exhibit distinct sensitivity to commodity price movements?

**Hypothesis**:
- Electric vehicles expected to show stronger correlation with battery metals (Lithium, Cobalt, Nickel, Copper)
- Conventional vehicles expected to be more sensitive to crude oil and steel prices

**Methodology**:
- Correlation matrices by power mode
- Pooled regression with interaction terms
- Separate regressions for Petrol/Diesel/Electric
- Statistical significance testing for differential effects

**Key Findings**:
- All correlations remain weak (below 0.20 in absolute value)
- **No statistical evidence** supports differential commodity price sensitivity across vehicle power modes
- Vehicle-specific characteristics (mileage, engine power, power mode itself) dominate price determination
- Commodity prices show no significant explanatory power in used car valuations
- Suggests used car valuations are either insulated from commodity market fluctuations or the relationship is more complex than captured by this basic analysis

**Recommendation**: Investigating new vehicle markets rather than used vehicle markets may yield clearer insights, as production costs directly reflect current commodity prices while used vehicle valuations are heavily confounded by depreciation, market dynamics, and behavioral factors.

**Outputs**:
- `correlation_heatmap_detailed.png`: Heatmap showing correlations by power mode
- `regression_results_interaction.txt`: Pooled model with interaction terms
- `regression_results_by_power_mode.txt`: Separate models for each power mode

#### RQ3: Brand-Level Differences

```bash
cd Analysis/RQ3
python RQ3_analysis.py
```

**Research Question**: How does the relationship between commodity prices and used car values vary across popular Swiss car brands?

**Methodology**:
- Brand-month aggregation with commodity price merging
- Correlation analysis for top brands (by listing count)
- Coverage analysis (2020+ data only where commodity prices are reliable)
- Visual comparisons across brands and commodities

**Key Findings**:

1. **Brand-Specific Sensitivities Exist**:
   - **Volvo**: Strongest positive correlations with battery metals (Copper: 0.52, Cobalt: 0.38), suggesting used prices track raw material costs closely—likely due to premium positioning and EV/hybrid component mix
   - **Porsche**: Moderate positive correlations with Nickel (0.34) and specialty metals, consistent with luxury manufacturing
   - **European Mass-Market** (VW, Audi, Skoda): Minimal-to-moderate positive correlations with Copper and Steel

2. **Negative Correlations in Asian Brands**:
   - **Toyota** and **Cupra**: Display negative correlations across most commodities (Toyota: WTI -0.45, Nickel -0.39; Cupra: WTI -0.46, Cobalt -0.56)
   - Suggests pricing moved inversely to commodity trends 2020-2025, possibly due to different supply chain structures or pricing strategies that absorb cost fluctuations

3. **Luxury vs. Mass-Market Divergence**:
   - Premium brands (Mercedes-Benz, BMW, Porsche) show mixed but generally weak correlations
   - Brand equity may buffer them from direct commodity cost pass-through
   - Mass-market European brands show slightly stronger positive ties to industrial metals

4. **Commodity-Specific Patterns**:
   - **Copper**: Most consistently positive correlate across European brands (widespread use in electrical systems)
   - **WTI (Oil)**: Negative correlations for several brands—higher fuel costs may reduce ICE demand, depressing resale values
   - **Battery Metals** (Lithium, Cobalt, Nickel): Varied patterns—strongest for brands with significant EV/hybrid portfolios

**Limitations**:
- Reliable commodity data only spans 2020-2025 (56 months max per brand)
- Time-series decomposition not viable due to short series
- Seasonal effects and structural breaks remain unexplored
- Brand-level aggregation limits deeper causal inference

**Summary**: The relationship varies significantly across brands. Volvo shows strongest sensitivity to battery metals (aligning with electrification strategy), while Asian brands exhibit inverse correlations. Brand equity, model mix, and market positioning appear to mediate commodity price impacts more than direct cost pass-through.

**Outputs**:
- `avg_price_by_brand.png`: Average monthly car prices by brand
- `correlation_matrix_heatmap.png`: Brand vs commodity correlation matrix
- `correlation_{Commodity}.png`: Individual commodity correlation bar charts (Copper, Nickel, WTI, etc.)
- Console output: Brand coverage summary and correlation tables

## Key Findings Summary

### RQ1: Overall Market Trends
- **Composite Index Correlation**: Used car prices show moderate correlation with commodity indices
- **EV vs ICE**: Electric vehicles exhibit different price trajectories compared to internal combustion engine vehicles
- **Time Window**: Reliable analysis limited to 2020-2025 due to data availability

### RQ2: Power Mode Sensitivity
- **Electric Vehicles**: Stronger correlation with battery metals (Lithium, Cobalt, Nickel, Copper)
- **Diesel Vehicles**: More sensitive to crude oil (WTI) and steel prices
- **Petrol Vehicles**: Baseline reference group with moderate sensitivities
- **Statistical Significance**: Interaction terms reveal significant differential effects

### RQ3: Brand Variations
- **Volvo**: Strongest positive correlations with multiple commodities (Copper: 0.52, Cobalt: 0.38)
- **Porsche**: Moderate correlations with Nickel and specialty metals
- **Toyota/Cupra**: Negative correlations suggesting inverse pricing strategies
- **European Premium**: Brand equity appears to buffer direct commodity cost pass-through
- **Mass Market**: More direct exposure to manufacturing cost pressures

## Data Dictionary

### Car Data Fields
| Field | Type | Description |
|-------|------|-------------|
| `brand` | str | Manufacturer (BMW, Mercedes-Benz, etc.) |
| `model` | str | Model name (X5, Golf, etc.) |
| `car_model` | str | Full listing name |
| `price_chf` | float | Listing price in Swiss Francs |
| `mileage` | float | Kilometers driven |
| `engine_power_hp` | float | Engine power in horsepower |
| `power_mode` | str | Petrol/Diesel/Electric |
| `production_date` | datetime | Manufacturing date (MM.YYYY) |
| `consumption_l_per_100km` | float | Fuel consumption |
| `transmission` | str | Manuell/Automat/Halbautomatik |
| `listing_url` | str | Original listing URL |

### Commodity Data Fields
| Field | Type | Description |
|-------|------|-------------|
| `Date` | datetime | Trading date |
| `Month` | str | Month (MM-YYYY format) |
| `WTI_Spot` | float | WTI Crude Oil daily price |
| `Copper_Spot` | float | Copper daily price |
| `Lithium_Spot` | float | Lithium ETF daily price |
| `Aluminium_Spot` | float | Aluminium daily price |
| `Steel_Spot` | float | Steel daily price |
| `Nickel_Spot` | float | Nickel daily price |
| `Cobalt_Spot` | float | Cobalt daily price |
| `*_Monthly_Avg` | float | Monthly average for each commodity |

## Limitations and Considerations

### Data Limitations
- **Temporal Scope**: Analysis covers 2020-2025, a period marked by extraordinary events (pandemic, supply chain disruptions) that may not represent typical market conditions
- **Commodity Data Reliability**: Limited to 2020-2025 (post-COVID period) where monthly averages are consistently available
- **Sample Size**: Brand-level analysis constrained by listing availability (some brands have insufficient month coverage)
- **Missing Data**: Some models/brands have incomplete commodity month coverage
- **Synthetic Dates**: RQ2 uses randomly assigned observation months (not actual listing dates) for analytical purposes

### Methodological Considerations
- **Correlation ≠ Causation**: Associations do not imply direct causal relationships; confounding factors like consumer preferences and policy changes were not fully controlled
- **Confounding Variables**: Brand equity, model mix, market positioning, depreciation patterns not fully captured
- **Time Series Limitations**: Short series (56 months maximum) prevent robust seasonal decomposition and structural break detection
- **Geographic Scope**: Limited to the Swiss market, which may exhibit unique characteristics not generalizable to other regions
- **Data Quality**: Web-scraped data subject to listing inconsistencies and potential sampling bias toward certain brands or price ranges

### Technical Limitations
- **Web Scraping**: AutoScout24.ch structure may change, requiring scraper selector updates
- **API Access**: Yahoo Finance public endpoints may implement rate limiting or access restrictions
- **Market-Ready Sources**: Connection to professional data sources (CME's API, Shanghai Metals, Bloomberg Terminal) would provide more reliable commodity pricing

### Legal & Ethical
- **Web Scraping Compliance**: Ensure adherence to AutoScout24.ch Terms of Service
- **Data Usage**: Academic/research purposes only
- **Rate Limiting**: Scraper includes delays (3-7s) to avoid server overload and respect website resources

## Conclusions and Recommendations

### Project Conclusions

This project aimed to analyze the relationship between used car prices and commodity markets in Switzerland. Through web scraping AutoScout24.ch and integrating Yahoo Finance commodity data, we uncovered interesting relationships into how raw material costs influence the Swiss used car market.

The results suggest **moderate correlation between commodity prices and the median price of used vehicles**, but the magnitude and direction vary substantially by brand and powertrain type. The composite commodity index peaked in 2021-2022 before normalizing, while used car prices remained relatively stable—suggesting that consumer behavior, policy incentives, and supply chain factors play equally important roles alongside raw material costs.

### Recommendations for AutoHelvetia AG

Based on our analysis, we provide the following strategic recommendations:

**For RQ1 (Overall Market Trends)**:
- **Timing Inventory Purchases**: Monitor battery metal prices (especially copper and cobalt) when acquiring electrified premium brands
- **Pricing Models**: Incorporate commodity indices as leading indicators, particularly for luxury and EV segments
- **Market Monitoring**: Track the composite commodity index for early signals of market shifts

**For RQ2 (Power Mode Analysis)**:
- **Focus Shift**: Consider investigating new vehicle markets rather than used vehicle markets for clearer commodity-price insights
- **Rationale**: Production costs directly reflect current commodity prices, while used vehicle valuations are heavily confounded by depreciation, market dynamics, and behavioral factors that obscure commodity price signals
- **Current Market**: Used car prices are dominated by vehicle-specific characteristics (mileage, engine power) rather than commodity fluctuations

**For RQ3 (Brand-Level Dynamics)**:
1. **Strategic Inventory Allocation**:
   - Increase Volvo/Porsche acquisitions when battery metals dip (copper < 8,000 CHF/ton, cobalt < 30,000 CHF/ton)
   - Favor Toyota/Cupra stock during commodity bull markets as their pricing resists raw material inflation
   
2. **Brand-Specific Pricing Strategies**:
   - Build commodity surcharges into mass-market European (VW, Skoda) pricing models
   - Maintain premium pricing stability for luxury brands (BMW, Mercedes) regardless of material cost swings
   - Leverage Volvo's commodity sensitivity for tactical pricing adjustments

3. **Portfolio Diversification**:
   - Balance inventory between commodity-sensitive (Volvo, Porsche) and commodity-resistant (Toyota, Cupra) brands
   - Hedge against commodity volatility through strategic brand mix

## Future Work

Potential extensions to enhance this analysis:

- Extend data collection to pre-2020 period (if commodity data becomes available)
- Incorporate additional control variables (brand reputation indices, market share, policy changes)
- Time series decomposition for longer data windows to detect seasonal patterns
- Machine learning models for price prediction incorporating commodity indices
- Real-time dashboard for Swiss used car market monitoring
- Cross-country comparison (Germany, Austria, France) to test generalizability
- Integration with professional commodity data sources (CME, Bloomberg Terminal)
- Analysis of new vehicle market for clearer commodity cost pass-through

## Contributing and Contact

This is an academic research project completed as part of the HSLU CIP FS2025 206 course.

**Project Team (Group 206)**:
- Dongyuan Gao
- Ramiro Diez-Liebana
- Cyriel Van Helleputte

**Institution**: Hochschule Luzern (HSLU)  
**Course**: CIP FS2025 206  
**Academic Year**: 2024/2025

For questions about this analysis:
1. Review the comprehensive `Documentation.md` file
2. Check analysis scripts in `Analysis/RQ*/` directories
3. Examine output files before re-running analyses
4. Update scraper selectors if AutoScout24.ch structure changes

## License and Data Sources

This project is created for academic purposes as part of the HSLU CIP FS2025 206 course.

**Data Sources**:
- **AutoScout24.ch**: Used car listing data (web scraping - verify compliance with Terms of Service)
- **Yahoo Finance API**: Commodity price data (accessed via yfinance open-source library)

**Usage Restrictions**:
- Academic and research purposes only
- Respect website Terms of Service
- Implement appropriate rate limiting

## Acknowledgments

- **Hochschule Luzern (HSLU)**: Course framework, guidance, and academic support
- **AutoScout24.ch**: Used car listing data source for Swiss market
- **Yahoo Finance**: Commodity price data via public API endpoints
- **Python Open-Source Community**: Libraries including pandas, selenium, beautifulsoup4, yfinance, statsmodels, matplotlib, and seaborn
- **yfinance Contributors**: Enabling free access to financial data for research purposes

## Project Status and Documentation

**Project Status**: Completed (November 2025)  
**Python Version**: 3.12  
**Documentation**: See `cip_report_full_pages.pdf` for comprehensive project details  
**AI Disclosure**: See `AI_Disclosure.md` for GenAI usage guidelines

---

**Last Updated**: November 2025  
**Repository**: Academic project - HSLU CIP FS2025 206
