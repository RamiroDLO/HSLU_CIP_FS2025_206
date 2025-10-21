"""
This script scrapes multiple pages of car listings, extracts data from a structured
JSON-LD block embedded in the page, and saves the results to CSV file.
"""
#%% Cell 1
import time
import json
import csv
import random
import logging
import undetected_chromedriver as uc
from typing import List, Dict, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

#%% Cell 2
# --- 1. CONFIGURATION & CONSTANTS ---
TARGET_COUNT = 500
OUTPUT_FILENAME = "autoscout_data_final.csv"
START_URL = "https://www.autoscout24.ch/de/autos/alle-marken"

# Configure logging at the module level for consistency
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

#%% Cell 3
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

#%% Cell 4
def scrape_page(driver) -> List[Dict]:
    """Extracts all listing data from the current page's structured JSON data."""
    listings_data = []
    try:
        logging.info("   Looking for structured JSON data on the page...")
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
                # id for merge url
                listing_url = item.get('url') or item.get('@id') or offers.get('url') or item_offered.get('url')

                data = {
                    'car_model': item.get('name', 'N/A'),
                    'price_chf': offers.get('price', 'N/A'),
                    'mileage': item_offered.get('mileageFromOdometer', {}).get('value', 'N/A'),
                    'engine_power_hp': vehicle_engine.get('enginePower', {}).get('value', 'N/A'),
                    'power_mode': extract_power_mode(vehicle_engine.get('fuelType', 'N/A')),
                    'listing_url': listing_url
                }
                listings_data.append(data)
            except Exception as e:
                logging.warning(f"   Could not parse one item in the JSON data: {e}")
                continue
        logging.info(f"   Successfully extracted {len(listings_data)} listings from JSON.")
    except TimeoutException:
        logging.error("   Timeout: Could not find the structured JSON data on the page.")
    except Exception as e:
        logging.error(f"   Error processing JSON data: {e}")
    return listings_data
#%% Cell 5
def scrape_page_2(driver) -> List[Dict]:
    """
    Extracts production_date, consumption_l_per_100km, and transmission
    from the DOM using icon <svg><title>…</title></svg> anchors.

    Returns a list of dicts with keys:
      - listing_url: canonical URL (from anchor href in the DOM)
      - production_date: string like '09.2022' or 'N/A'
      - consumption_l_per_100km: float (e.g., 13.4) or 'N/A'
      - transmission: normalized string ('Automat', 'Manuell', or raw variant)
      - raw_values: dict of raw extracted strings for debugging
    """
    results: List[Dict] = []

    try:
        # Each listing container
        containers = driver.find_elements(By.CSS_SELECTOR, "div.chakra-stack.css-5cam7h")
        if not containers:
            containers = driver.find_elements(By.CSS_SELECTOR, "div.chakra-stack")
    except Exception as e:
        logging.warning(f"scrape_page_2: could not locate containers: {e}")
        containers = []

    def _normalize_transmission(raw: str) -> str:
        if not raw:
            return "N/A"
        txt = raw.strip().lower()
        # German and English variants
        if any(k in txt for k in ("automat", "automatic", "automatik", "automatikgetriebe")):
            return "Automat"
        if any(k in txt for k in ("manuell", "manual", "schalt", "schaltgetriebe")):
            return "Manuell"
        if "halbautomatisches" in txt or "halbautomatik" in txt:
            return "Halbautomatik"
        return raw.strip()

    import re
    for idx, container in enumerate(containers):
        try:
            listing_url = None
            prod_date = "N/A"
            consumption_val = "N/A"
            transmission = "N/A"
            raw_vals = {"production_raw": None, "consumption_raw": None,
                        "transmission_raw": None, "listing_href": None}

            # Try to extract a stable listing URL from anchor
            try:
                link_el = container.find_element(By.XPATH, ".//a[@href]")
                href = link_el.get_attribute('href')
                if href and "/de/d/" in href:  # heuristic: listing pages contain /de/d/
                    listing_url = href.split("?")[0]  # strip tracking params
                    raw_vals["listing_href"] = listing_url
            except Exception:
                pass

            # Helper: find <svg><title>…</title></svg> and its adjacent <p>
            def _extract_after_svg_title(svg_title_text: str) -> Optional[str]:
                try:
                    svg = container.find_element(
                        By.XPATH, f".//svg[./title[contains(normalize-space(), '{svg_title_text}')]]"
                    )
                    # Prefer sibling <p>
                    try:
                        p = svg.find_element(By.XPATH, "./parent::*/following-sibling::p[1]")
                    except Exception:
                        p = svg.find_element(By.XPATH, "./following::p[1]")
                    return p.text.strip() if p.text else None
                except Exception:
                    return None

            # Production date
            raw_prod = _extract_after_svg_title("Calendar")
            if raw_prod:
                prod_date = raw_prod
                raw_vals["production_raw"] = raw_prod

            # Consumption
            raw_cons = _extract_after_svg_title("Consumption")
            if raw_cons:
                raw_vals["consumption_raw"] = raw_cons
                m = re.search(r"([\d\.,]+)", raw_cons)
                if m:
                    num = m.group(1).replace(",", ".")
                    try:
                        consumption_val = float(num)
                    except Exception:
                        consumption_val = "N/A"

            # Transmission
            raw_trans = _extract_after_svg_title("Transmission")
            if raw_trans:
                raw_vals["transmission_raw"] = raw_trans
                transmission = _normalize_transmission(raw_trans)

            results.append({
                "listing_url": listing_url or f"dom_idx_{idx}",
                "production_date": prod_date,
                "consumption_l_per_100km": consumption_val,
                "transmission": transmission,
                # "raw_values": raw_vals
            })

        except Exception as e:
            logging.warning(f"scrape_page_2: failed for container idx {idx}: {e}")
            continue

    logging.info(f"scrape_page_2: extracted {len(results)} DOM/icon entries from page.")
    return results

#%% Cell 6
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

#%% Cell 7
def save_to_csv(data: List[Dict], filename: str):
    """Saves the collected data to CSV file."""
    if not data:
        logging.warning("No data was collected to save.")
        return

    logging.info(f"--- Saving {len(data)} listings to {filename}... ---")
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'car_model',
                'price_chf',
                'mileage',
                'engine_power_hp',
                'power_mode',
                # NEW columns:
                'production_date',
                'consumption_l_per_100km',
                'transmission'
                # Optional debug column:
                #'raw_values'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        logging.info(f"   ✅ Successfully saved data to {filename}")
    except Exception as e:
        logging.error(f"   ❌ Failed to save data to CSV: {e}")

#%% Cell 8
# --- 3. MAIN SCRAPER ORCHESTRATION ---

# In your long_test.py file, replace the entire run_scraper function

def run_scraper():
    """Main function to orchestrate the entire scraping process."""
    all_collected_data = []
    page_count = 0
    driver = None

    try:
        logging.info("--- 1. Setting up the browser with simplified options ---")
        options = uc.ChromeOptions()
        # Using a minimal, stable set of options to prevent crashes
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # You can also add --headless if you don't want to see the window
        # options.add_argument("--headless")

        driver = uc.Chrome(options=options)
        logging.info("   ✅ Browser is up. Pausing for 5 seconds to observe...")
        time.sleep(5)  # This pause lets us see if the browser stays open on its own

        logging.info(f"--- 2. Navigating to {START_URL} ---")
        driver.get(START_URL)
        try:
            wait = WebDriverWait(driver, 15)
            accept_button = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
            driver.execute_script("arguments[0].click();", accept_button)
            logging.info("   ✅ Cookie banner clicked.")
            time.sleep(3)
        except TimeoutException:
            logging.warning("   ⚠️ Cookie banner not found, continuing.")

        logging.info("--- 3. Stabilizing the page with a refresh... ---")
        driver.refresh()
        WebDriverWait(driver, 15).until(lambda d: d.execute_script("return document.readyState") == "complete")
        logging.info("   ✅ Page is ready.")
# %% Cell 9
        # Main scraping loop
        while len(all_collected_data) < TARGET_COUNT:
            page_count += 1
            logging.info(f"--- Scraping Page {page_count} ---")

            page_data = scrape_page(driver)
            if not page_data:
                logging.warning("   No data found on this page. Stopping.")
                break
            # NEW: scrape DOM/icon-based fields for the current page
            dom_data = scrape_page_2(driver)

            # NEW: build lookup map by listing_url
            dom_map = {d['listing_url']: d for d in dom_data if d.get('listing_url')}

            merged_page_data = []
            for idx, json_item in enumerate(page_data):
                listing_url = json_item.get('listing_url')
                dom_row = dom_map.get(listing_url)

                # Fallback: if JSON has no listing_url, try index-based alignment and log it
                if not dom_row and not listing_url and idx < len(dom_data):
                    dom_row = dom_data[idx]
                    logging.info(f"   Index fallback used for page item idx {idx}")

                # Merge: keep JSON fields; fill new ones from DOM (or N/A)
                json_item['production_date'] = json_item.get(
                    'production_date',
                    dom_row.get('production_date') if dom_row else "N/A"
                )
                json_item['consumption_l_per_100km'] = json_item.get(
                    'consumption_l_per_100km',
                    dom_row.get('consumption_l_per_100km') if dom_row else "N/A"
                )
                json_item['transmission'] = json_item.get(
                    'transmission',
                    dom_row.get('transmission') if dom_row else "N/A"
                )

                # Optional: keep raw DOM values for debugging/auditing
                if dom_row and dom_row.get('raw_values'):
                    json_item['raw_values'] = dom_row['raw_values']

                merged_page_data.append(json_item)

            # NEW: Replace page_data for downstream processing
            page_data = merged_page_data

            # Optional: log counts for visibility
            logging.info(f"   Merge: JSON {len(merged_page_data)}, DOM {len(dom_data)}")

            all_collected_data.extend(page_data)
            logging.info(f"   Collected {len(all_collected_data)}/{TARGET_COUNT} total listings.")

            if len(all_collected_data) >= TARGET_COUNT:
                logging.info("   Target reached!")
                break

            if not navigate_to_next_page(driver):
                break

            pause_duration = random.uniform(5.0, 10.0)
            logging.info(f"   Pausing for {pause_duration:.2f} seconds before next page...")
            time.sleep(pause_duration)

    except KeyboardInterrupt:
        logging.warning("--- Process interrupted by user. ---")
    except Exception as e:
        logging.error(f"❌ A fatal error occurred: {e}", exc_info=True)
    finally:
        save_to_csv(all_collected_data, OUTPUT_FILENAME)
        if driver:
            logging.info("--- Closing browser... ---")
            driver.quit()
            logging.info("   ✅ Browser closed.")
# %% Cell 10
# --- 4. EXECUTION ---

if __name__ == "__main__":
    run_scraper()