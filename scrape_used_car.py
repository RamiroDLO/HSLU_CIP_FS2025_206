"""
This script scrapes multiple pages of car listings from AutoScout24,
extracts data from both a structured JSON-LD block and from visible DOM elements,
merges them, and saves the results to a CSV file.
"""

import time
import json
import csv
import random
import logging
import re
import undetected_chromedriver as uc
from typing import List, Dict
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# --- 1. CONFIGURATION & CONSTANTS ---

TARGET_COUNT = 500
OUTPUT_FILENAME = "autoscout_data_final.csv"
START_URL = "https://www.autoscout24.ch/de/autos/alle-marken"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log', mode='w'),
        logging.StreamHandler()
    ]
)

# --- 2. HELPER FUNCTIONS ---

def extract_power_mode(fuel_type_text: str) -> str:
    """Standardizes the fuel type string from the JSON data."""
    if not fuel_type_text:
        return "N/A"

    text_lower = fuel_type_text.lower()
    if 'benzin' in text_lower or 'petrol' in text_lower:
        return "Benzin"
    if 'diesel' in text_lower:
        return "Diesel"
    if 'elektro' in text_lower or 'electric' in text_lower:
        return "Elektro"
    if 'hybrid' in text_lower:
        return "Hybrid"
    return "N/A"

def _normalize_transmission(raw: str) -> str:
    """Normalizes transmission type strings."""
    if not raw:
        return "N/A"

    txt = raw.strip().lower()
    if any(k in txt for k in ("automat", "automatic", "automatik", "automatikgetriebe")):
        return "Automat"
    if any(k in txt for k in ("manuell", "manual", "schalt", "schaltgetriebe")):
        return "Manuell"
    if any(k in txt for k in ("halbautomatisches", "halbautomatik", "halbautomatikgetriebe")):
        return "Halbautomatik"
    return raw.strip()

# --- 3. SCRAPING FUNCTIONS ---

def scrape_page_json(driver) -> List[Dict]:
    """Extracts all listing data from the current page's structured JSON-LD data."""
    listings_data = []

    try:
        logging.info(" Looking for structured JSON data on the page...")
        wait = WebDriverWait(driver, 15)
        script_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "script[data-testid='structured-schema-srp']"))
        )

        json_text = script_element.get_attribute('innerHTML')
        structured_data = json.loads(json_text)
        car_list = structured_data.get('mainEntity', {}).get('offers', {}).get('itemListElement', [])

        for item in car_list:
            try:
                offers = item.get('offers', {})
                item_offered = offers.get('itemOffered', {})
                vehicle_engine = item_offered.get('vehicleEngine', {})

                listing_url = item.get('url') or item.get('@id') or offers.get('url') or item_offered.get('url')

                data = {
                    'car_model': item.get('name', 'N/A'),
                    'price_chf': offers.get('price', 'N/A'),
                    'mileage': item_offered.get('mileageFromOdometer', {}).get('value', 'N/A'),
                    'engine_power_hp': vehicle_engine.get('enginePower', {}).get('value', 'N/A'),
                    'power_mode': extract_power_mode(vehicle_engine.get('fuelType', 'N/A')),
                    'listing_url': listing_url.split("?")[0] if listing_url else 'N/A'
                }
                listings_data.append(data)

            except Exception as e:
                logging.warning(f" Could not parse one item in the JSON data: {e}")
                continue

        logging.info(f" Successfully extracted {len(listings_data)} listings from JSON.")

    except TimeoutException:
        logging.error(" Timeout: Could not find the structured JSON data on the page.")
    except Exception as e:
        logging.error(f" Error processing JSON data: {e}")

    return listings_data

def scrape_page_icons(driver) -> list[dict]:
    """Extracts icon-related data by iterating through each car listing container."""
    results = []

    def extract_icon_value(listing_element, icon_title: str) -> str:
        """Extract value for a specific icon within a listing container"""
        try:
            icon_svg = listing_element.find_element(
                By.XPATH,
                f".//svg[.//title[text()='{icon_title}']]"
            )
            value_p_tag = icon_svg.find_element(By.XPATH, "./following-sibling::p")
            txt = (value_p_tag.text or "").strip()
            return txt if txt and txt != "-" else "N/A"
        except Exception:
            return "N/A"

    # Enhanced container detection with fallbacks
    try:
        car_listing_elements = driver.find_elements(By.CSS_SELECTOR, "article[data-testid='listing-card']")
        logging.info(f"Found {len(car_listing_elements)} car listing containers")

        if not car_listing_elements:
            fallback_selectors = [
                "article",
                "div[data-testid*='listing']",
                "div[class*='listing']",
                "div[class*='card']"
            ]
            for selector in fallback_selectors:
                car_listing_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if car_listing_elements:
                    logging.info(f"Found {len(car_listing_elements)} containers with fallback: {selector}")
                    break

    except Exception as e:
        logging.error(f"Could not find car listing containers: {e}")
        return []

    for listing_element in car_listing_elements:
        listing_data = {
            "production_date": "N/A",
            "consumption_l_per_100km": "N/A",
            "transmission": "N/A",
            "listing_url": "N/A"
        }

        # Extract listing URL
        try:
            link_element = listing_element.find_element(By.XPATH, ".//a[contains(@href, '/de/d/')]")
            href = link_element.get_attribute('href')
            if href:
                listing_data["listing_url"] = href.split("?")[0]
        except NoSuchElementException:
            logging.debug(" Listing URL not found for this article.")

        # Extract icon data using improved function
        listing_data["production_date"] = extract_icon_value(listing_element, "Calendar icon")
        listing_data["consumption_l_per_100km"] = extract_icon_value(listing_element, "Consumption icon")
        listing_data["transmission"] = extract_icon_value(listing_element, "Transmission icon")

        # Process consumption data
        raw_cons = listing_data["consumption_l_per_100km"]
        if raw_cons != "N/A":
            m = re.search(r"([\d\.,]+)", raw_cons)
            if m:
                num = m.group(1).replace(",", ".")
                try:
                    val = float(num)
                    listing_data["consumption_l_per_100km"] = val if 1 <= val <= 50 else "N/A"
                except ValueError:
                    listing_data["consumption_l_per_100km"] = "N/A"

        # Normalize transmission
        listing_data["transmission"] = _normalize_transmission(listing_data["transmission"])
        results.append(listing_data)

    logging.info(f"Successfully extracted icon data for {len(results)} listings.")
    return results

def navigate_to_next_page(driver) -> bool:
    """Navigates to the next page and waits for it to be ready."""
    try:
        next_selectors = ["[data-testid='pagination-next']", "[aria-label*='next']"]
        next_button = None
        for selector in next_selectors:
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, selector)
                if next_button.is_enabled():
                    break
            except NoSuchElementException:
                continue

        if next_button and next_button.is_enabled():
            logging.info("   Next page button found. Clicking...")
            driver.execute_script("arguments[0].click();", next_button)

            logging.info("   Waiting for new page to become interactive...")
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            logging.info("   Next page is ready.")
            return True
        else:
            logging.info("   No next page button found. Ending pagination.")
            return False
    except Exception as e:
        logging.error(f"   An unexpected error occurred during pagination: {e}")
        return False


def save_to_csv(data: List[Dict], filename: str):
    """Saves the collected data to a CSV file."""
    if not data:
        logging.warning("No data was collected to save.")
        return

    logging.info(f"--- Saving {len(data)} listings to {filename}... ---")
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'car_model', 'price_chf', 'mileage', 'engine_power_hp', 'power_mode',
                'production_date', 'consumption_l_per_100km', 'transmission', 'listing_url'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        logging.info(f" ✅ Successfully saved data to {filename}")
    except Exception as e:
        logging.error(f" ❌ Failed to save data to CSV: {e}")

# --- 4. MAIN SCRAPER ORCHESTRATION ---

def run_scraper():
    """Main function to orchestrate the entire scraping process."""
    all_collected_data = []
    page_count = 0
    driver = None

    try:
        logging.info("--- 1. Setting up the browser ---")
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = uc.Chrome(options=options)
        logging.info(" ✅ Browser is up.")

        logging.info(f"--- 2. Navigating to {START_URL} ---")
        driver.get(START_URL)

        # Handle cookie banner
        try:
            wait = WebDriverWait(driver, 15)
            accept_button = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
            driver.execute_script("arguments[0].click();", accept_button)
            logging.info(" ✅ Cookie banner clicked.")
            time.sleep(3)
        except TimeoutException:
            logging.warning(" ⚠️ Cookie banner not found, continuing.")

        # Main scraping loop
        while len(all_collected_data) < TARGET_COUNT:
            page_count += 1
            logging.info(f"--- Scraping Page {page_count} ---")

            WebDriverWait(driver, 15).until(lambda d: d.execute_script("return document.readyState") == "complete")
            logging.info(" Page is ready.")

            json_data = scrape_page_json(driver)
            if not json_data:
                logging.warning(" No JSON-LD data found on this page. Stopping.")
                break

            icon_data = scrape_page_icons(driver)
            icon_data_map = {item["listing_url"]: item for item in icon_data if item.get("listing_url") != "N/A"}

            merged_page_data = []
            for json_item in json_data:
                listing_url = json_item.get("listing_url")
                if listing_url and listing_url in icon_data_map:
                    json_item.update(icon_data_map[listing_url])
                    merged_page_data.append(json_item)

            all_collected_data.extend(merged_page_data)
            logging.info(f" Collected {len(all_collected_data)}/{TARGET_COUNT} total listings.")

            if len(all_collected_data) >= TARGET_COUNT:
                logging.info(" Target reached!")
                break

            if not navigate_to_next_page(driver):
                break

            pause_duration = random.uniform(3.0, 7.0)
            logging.info(f" Pausing for {pause_duration:.2f} seconds before next page...")
            time.sleep(pause_duration)

    except KeyboardInterrupt:
        logging.warning("--- Process interrupted by user. ---")
    except Exception as e:
        logging.critical(f"❌ A fatal error occurred in run_scraper: {e}", exc_info=True)
    finally:
        if all_collected_data:
            save_to_csv(all_collected_data, OUTPUT_FILENAME)

        if driver:
            logging.info("--- Closing browser... ---")
            driver.quit()
            logging.info(" ✅ Browser closed.")

# --- 5. EXECUTION ---

if __name__ == "__main__":
    run_scraper()