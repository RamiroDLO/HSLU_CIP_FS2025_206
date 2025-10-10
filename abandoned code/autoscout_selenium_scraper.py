#!/usr/bin/env python3
"""
AutoScout24.ch Web Scraper using Selenium
Collects car listing data for depreciation analysis

Requirements:
- Selenium WebDriver
- Chrome browser
- Rate limiting (1 request per 3 seconds)
- Target: 5000 listings
- Data fields: car_model, engine_power_hp, power_mode, mileage, price_chf
"""

import csv
import json
import time
import re
import logging
import random
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from bs4 import BeautifulSoup, Tag

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('autoscout_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoScoutScraper:
    def __init__(self):
        """Initialize the AutoScout24 scraper"""
        self.collected_data = []

    def extract_number_from_text(self, text: str) -> Optional[int]:
        """Extract numeric value from text string"""
        if not text or text.strip() == "":
            return None
        
        # Remove common non-numeric characters and extract numbers
        numbers = re.findall(r'\d+', text.replace("'", "").replace(",", "").replace(".", ""))
        if numbers:
            return int(''.join(numbers))
        return None
    
    def extract_power_mode(self, text: str) -> str:
        """Extract power mode (Benzin, Diesel, Elektro, Hybrid) from text"""
        if not text:
            return "N/A"
        
        text_lower = text.lower()
        if any(keyword in text_lower for keyword in ['benzin', 'petrol', 'gasoline']):
            return "Benzin"
        elif any(keyword in text_lower for keyword in ['diesel']):
            return "Diesel"
        elif any(keyword in text_lower for keyword in ['elektro', 'electric', 'ev']):
            return "Elektro"
        elif any(keyword in text_lower for keyword in ['hybrid']):
            return "Hybrid"
        else:
            return "N/A"

    # In autoscout_selenium_scraper.py

    def get_listings_on_page(self, driver) -> List[Dict]:
        """Extracts all listing data from the page's structured JSON data."""
        listings_data = []
        try:
            logger.info("Looking for structured JSON data on the page...")
            wait = WebDriverWait(driver, 15)

            # Step 1: Wait for and find the specific <script> tag
            script_element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "script[data-testid='structured-schema-srp']"))
            )

            # Step 2: Extract the text from the tag and parse it as JSON
            json_text = script_element.get_attribute('innerHTML')
            structured_data = json.loads(json_text)
            logger.info("Structured JSON data found and parsed.")

            # Step 3: Navigate through the JSON to the list of cars
            car_list = structured_data.get('mainEntity', {}).get('offers', {}).get('itemListElement', [])

            # Step 4: Loop through each car in the JSON list and extract its data
            for item in car_list:
                try:
                    offers = item.get('offers', {})
                    item_offered = offers.get('itemOffered', {})
                    vehicle_engine = item_offered.get('vehicleEngine', {})

                    data = {
                        'car_model': item.get('name', 'N/A'),
                        'price_chf': offers.get('price', 'N/A'),
                        'mileage': item_offered.get('mileageFromOdometer', {}).get('value', 'N/A'),
                        'engine_power_hp': vehicle_engine.get('enginePower', {}).get('value', 'N/A'),
                        'power_mode': self.extract_power_mode(vehicle_engine.get('fuelType', 'N/A'))
                    }
                    listings_data.append(data)
                except Exception as e:
                    logger.warning(f"Could not parse one of the items in the JSON data: {e}")
                    continue

            logger.info(f"Successfully extracted {len(listings_data)} listings from JSON data.")

        except TimeoutException:
            logger.error("Timeout: Could not find the structured JSON data script tag on the page.")
        except Exception as e:
            logger.error(f"Error processing JSON data on page: {e}")

        return listings_data

    # In autoscout_selenium_scraper.py, replace the entire function

    def navigate_to_next_page(self, driver) -> bool:
        """Navigate to the next page of results with a more robust wait."""
        try:
            next_button = None
            next_selectors = [
                "[data-testid='pagination-next']",
                "[aria-label*='next']"
            ]

            for selector in next_selectors:
                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, selector)
                    if next_button.is_enabled():
                        break
                except NoSuchElementException:
                    continue

            if next_button and next_button.is_enabled():
                logger.info("Next page button found. Clicking...")
                driver.execute_script("arguments[0].click();", next_button)

                # --- CORRECTED WAIT CONDITION ---
                logger.info("Waiting for next page to become interactive...")
                WebDriverWait(driver, 15).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                logger.info("Next page is ready.")
                return True
            else:
                logger.info("No next page button found. Ending pagination.")
                return False

        except Exception as e:
            logger.error(f"An unexpected error occurred during pagination: {e}")
            return False
    
    def save_data_to_csv(self, data: List[Dict], filename: str = "autoscout_data.csv"):
        """Save collected data to CSV file"""
        if not data:
            logger.warning("No data to save")
            return
        
        try:
            fieldnames = ['car_model', 'engine_power_hp', 'power_mode', 'mileage', 'price_chf']
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            logger.info(f"Successfully saved {len(data)} listings to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving data to CSV: {e}")


def main():
    """Main function to run the scraper - kept for compatibility"""
    print("Note: This standalone scraper is deprecated. Use execute_scraping.py instead.")
    print("AutoScout24.ch Web Scraper")
    print("=" * 40)

    # Create scraper instance (no parameters needed now)
    scraper = AutoScoutScraper()

    try:
        print("This scraper now works through the orchestrator.")
        print("Run execute_scraping.py instead.")

    except Exception as e:
        print(f"Error: {e}")
        logger.error(f"Main execution error: {e}")


if __name__ == "__main__":
    main()