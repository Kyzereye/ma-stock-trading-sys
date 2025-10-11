# Stock Data Scraper for StockAnalysis.com

This project provides Python scripts to scrape historical stock data from StockAnalysis.com. It includes multiple approaches to handle different scenarios and requirements.

## Files

- `simple_scraper.py` - Basic scraper using requests and BeautifulSoup
- `stock_scraper.py` - Intermediate scraper with URL manipulation for date ranges
- `advanced_scraper.py` - Advanced scraper using Selenium for JavaScript interaction
- `requirements.txt` - Python dependencies

## Installation

1. Install the required packages:
```bash
pip install -r requirements.txt
```

2. For the advanced scraper with Selenium, you'll also need Chrome WebDriver:
   - On macOS: `brew install chromedriver`
   - Or use webdriver-manager (included in requirements.txt)

## Usage

### Simple Scraper (Recommended for basic use)

```python
from simple_scraper import SimpleStockScraper

scraper = SimpleStockScraper()
df = scraper.get_stock_data("A")  # Get data for Agilent Technologies
scraper.save_to_csv(df, "A")
```

### Advanced Scraper (For date range selection)

```python
from advanced_scraper import AdvancedStockAnalysisScraper

scraper = AdvancedStockAnalysisScraper(use_selenium=True)
df = scraper.get_stock_data("A", period="1y")  # Get 1 year of data
scraper.save_to_csv(df, "A")
scraper.close()  # Don't forget to close the browser
```

## Features

- **Multiple scraping approaches**: Choose between simple requests or Selenium-based scraping
- **Date range selection**: Attempts to change from 6 months to 1 year data
- **Data cleaning**: Automatically cleans and formats the scraped data
- **CSV export**: Saves data to CSV files for easy analysis
- **Error handling**: Robust error handling for network and parsing issues

## Data Format

The scraper extracts the following columns:
- Date
- Open
- High
- Low
- Close
- Adj. Close
- Change (percentage)
- Volume

## Notes

- The website may have anti-bot measures, so use reasonable delays between requests
- The advanced scraper with Selenium can handle JavaScript interactions but requires more resources
- The simple scraper is more lightweight but may not handle all date range selections
- Always respect the website's terms of service and robots.txt

## Example Output

```
Fetching data for A...
Successfully extracted 50 rows of data

Data preview:
        Date    Open    High     Low   Close  Adj. Close  Change     Volume
0 2025-09-19  128.28  128.55  126.02  126.32      126.32   -1.02  2827790
1 2025-09-18  127.76  128.54  126.76  127.62      127.62    0.71  1513336
2 2025-09-17  127.72  130.08  126.38  126.72      126.72   -0.37  1921728
...
```
# stock_download
