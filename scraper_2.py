"""
FIXED MARKDOWN-BASED VERSION of AutoScout24 scraper
Fixes: Added proper waits, debugging, and fallback strategies
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log', mode='w'),
        logging.StreamHandler()
    ]
)

# Configuration
TARGET_COUNT = 20
OUTPUT_FILENAME = "autoscout_data_final.csv"
START_URL = "https://www.autoscout24.ch/de/autos/alle-marken"


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
                logging.warning(f"   Could not parse one item in the JSON data: {e}")
                continue
        logging.info(f"   Successfully extracted {len(listings_data)} listings from JSON.")
    except TimeoutException:
        logging.error("   Timeout: Could not find the structured JSON data on the page.")
    except Exception as e:
        logging.error(f"   Error processing JSON data: {e}")
    return listings_data


def scrape_page_2(driver) -> List[Dict]:
    """
    FIXED MARKDOWN-BASED APPROACH with proper waits and debugging
    """
    results = []

    try:
        logging.info("   Preparing to extract article data...")

        # FIX 1: Scroll to trigger lazy loading and ensure content is rendered
        logging.info("   Scrolling to trigger lazy loading...")
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 1600);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)

        # FIX 2: Wait explicitly for article containers to be present
        logging.info("   Waiting for article containers to load...")
        wait = WebDriverWait(driver, 20)

        try:
            # Wait for at least one article to be present
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "article[data-testid='listing-card']")))
            logging.info("   ✅ Article containers detected!")
        except TimeoutException:
            logging.error("   ❌ Timeout waiting for article containers!")

            # FIX 3: Try alternative selectors
            logging.info("   Trying alternative selectors...")

            # Try without data-testid
            articles_alt = driver.find_elements(By.CSS_SELECTOR, "article")
            if articles_alt:
                logging.info(f"   Found {len(articles_alt)} <article> elements (without data-testid)")

            # Save page source for debugging
            try:
                with open('debug_page_source.html', 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                logging.info("   Saved page source to debug_page_source.html for inspection")
            except:
                pass

            return []

        # FIX 4: Get all article containers
        articles = driver.find_elements(By.CSS_SELECTOR, "article[data-testid='listing-card']")
        logging.info(f"   Found {len(articles)} article containers")

        if not articles:
            logging.error("   No articles found! This should not happen after wait succeeded.")
            return []

        # Process each article
        for idx, article in enumerate(articles):
            listing_data = {
                "listing_url": "N/A",
                "production_date": "N/A",
                "consumption_l_per_100km": "N/A",
                "transmission": "N/A"
            }

            # Extract listing URL
            try:
                link = article.find_element(By.XPATH, ".//a[contains(@href, '/de/d/')]")
                href = link.get_attribute('href')
                if href:
                    listing_data["listing_url"] = href.split("?")[0]
            except NoSuchElementException:
                logging.debug(f"   Article {idx+1}: No listing URL found")

            # Get article text for parsing
            try:
                article_text = article.text

                if not article_text or len(article_text) < 50:
                    logging.warning(f"   Article {idx+1}: Text is empty or too short ({len(article_text)} chars)")
                    continue

                # Debug: Log first 200 chars of article text for first article
                if idx == 0:
                    logging.info(f"   Sample article text (first 200 chars): {article_text[:200]}")

                # Parse production date
                calendar_match = re.search(r'Calendar icon\s+(\d{2}\.\d{4})', article_text)
                if calendar_match:
                    listing_data["production_date"] = calendar_match.group(1)
                    logging.debug(f"   Article {idx+1}: production_date = '{calendar_match.group(1)}'")
                else:
                    # Try alternative pattern (just the date without "Calendar icon")
                    date_match = re.search(r'\b(\d{2}\.\d{4})\b', article_text)
                    if date_match:
                        listing_data["production_date"] = date_match.group(1)
                        logging.debug(f"   Article {idx+1}: production_date = '{date_match.group(1)}' (fallback)")

                # Parse transmission
                transmission_match = re.search(r'Transmission icon\s+(\w+)', article_text)
                if transmission_match:
                    raw_transmission = transmission_match.group(1)
                    listing_data["transmission"] = _normalize_transmission(raw_transmission)
                    logging.debug(f"   Article {idx+1}: transmission = '{listing_data['transmission']}'")
                else:
                    # Try alternative pattern (look for Automat/Manuell directly)
                    trans_alt = re.search(r'\b(Automat|Manuell|Halbautomatik)\b', article_text)
                    if trans_alt:
                        listing_data["transmission"] = trans_alt.group(1)
                        logging.debug(f"   Article {idx+1}: transmission = '{trans_alt.group(1)}' (fallback)")

                # Parse consumption
                consumption_match = re.search(r'Consumption icon\s+([\d\.,]+\s*l/100\s*km|[-–])', article_text)
                if consumption_match:
                    raw_consumption = consumption_match.group(1)
                    if raw_consumption not in ['-', '–']:
                        num_match = re.search(r'([\d\.,]+)', raw_consumption)
                        if num_match:
                            num = num_match.group(1).replace(",", ".")
                            try:
                                val = float(num)
                                listing_data["consumption_l_per_100km"] = val if 1 <= val <= 50 else "N/A"
                                logging.debug(f"   Article {idx+1}: consumption = '{val}'")
                            except ValueError:
                                listing_data["consumption_l_per_100km"] = "N/A"
                    else:
                        listing_data["consumption_l_per_100km"] = "N/A"
                        logging.debug(f"   Article {idx+1}: consumption = N/A (dash)")
                else:
                    # Try alternative pattern (just number + l/100 km)
                    cons_alt = re.search(r'([\d\.,]+)\s*l/100\s*km', article_text)
                    if cons_alt:
                        num = cons_alt.group(1).replace(",", ".")
                        try:
                            val = float(num)
                            listing_data["consumption_l_per_100km"] = val if 1 <= val <= 50 else "N/A"
                            logging.debug(f"   Article {idx+1}: consumption = '{val}' (fallback)")
                        except ValueError:
                            pass

            except Exception as e:
                logging.warning(f"   Article {idx+1}: Error parsing text: {e}")

            results.append(listing_data)

            # Log progress
            if (idx + 1) % 5 == 0:
                logging.info(f"   Processed {idx + 1}/{len(articles)} articles")

        logging.info(f"   scrape_page_2: Successfully extracted data for {len(results)} listings")

        # FIX 5: More accurate success rate calculation
        success_count = sum(1 for r in results if r["production_date"] != "N/A")
        trans_count = sum(1 for r in results if r["transmission"] != "N/A")
        cons_count = sum(1 for r in results if r["consumption_l_per_100km"] != "N/A")

        logging.info(f"   Success rate:")
        logging.info(f"     - production_date: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
        logging.info(f"     - transmission: {trans_count}/{len(results)} ({trans_count/len(results)*100:.1f}%)")
        logging.info(f"     - consumption: {cons_count}/{len(results)} ({cons_count/len(results)*100:.1f}%)")

        # Warning if success rate is too low
        if success_count < len(results) * 0.5:
            logging.warning(f"   ⚠️ Low success rate for production_date! Check if page structure changed.")

    except Exception as e:
        logging.error(f"   Error in scrape_page_2: {e}", exc_info=True)

    return results


def navigate_to_next_page(driver) -> bool:
    """Navigates to the next page and waits for it to be ready."""
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='pagination-next']")
        if next_button and next_button.is_enabled():
            logging.info("   Next page button found. Clicking...")
            driver.execute_script("arguments[0].click();", next_button)

            # Wait for page to load
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

            # Additional wait for dynamic content
            time.sleep(3)

            logging.info("   Next page is ready.")
            return True
        else:
            logging.info("   No enabled next page button found. Ending pagination.")
            return False
    except NoSuchElementException:
        logging.info("   No next page button found. Ending pagination.")
        return False
    except Exception as e:
        logging.error(f"   An unexpected error occurred during pagination: {e}")
        return False


def save_to_csv(data: List[Dict], filename: str):
    """Saves the collected data to CSV file with accurate statistics."""
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
        logging.info(f"   ✅ Successfully saved data to {filename}")

        # FIXED: Accurate statistics (don't count N/A as success)
        total = len(data)
        with_date = sum(1 for d in data if d.get('production_date', 'N/A') != 'N/A')
        with_consumption = sum(1 for d in data if d.get('consumption_l_per_100km', 'N/A') != 'N/A')
        with_transmission = sum(1 for d in data if d.get('transmission', 'N/A') != 'N/A')

        logging.info(f"   📊 Final Statistics (excluding N/A):")
        logging.info(f"     - production_date: {with_date}/{total} ({with_date/total*100:.1f}%)")
        logging.info(f"     - consumption: {with_consumption}/{total} ({with_consumption/total*100:.1f}%)")
        logging.info(f"     - transmission: {with_transmission}/{total} ({with_transmission/total*100:.1f}%)")

        if with_date == 0 or with_transmission == 0:
            logging.error(f"   ❌ CRITICAL: All values are N/A! Scraping failed!")
        elif with_date < total * 0.8:
            logging.warning(f"   ⚠️ WARNING: Success rate is below 80%!")
        else:
            logging.info(f"   ✅ SUCCESS: Data extraction worked!")

    except Exception as e:
        logging.error(f"   ❌ Failed to save data to CSV: {e}")


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
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--start-maximized")

        # For macOS compatibility
        driver = uc.Chrome(
            options=options,
            use_subprocess=True,
            suppress_welcome=True
        )

        logging.info("   ✅ Browser is up.")

        # Wait for browser to stabilize
        logging.info("   Waiting for browser to stabilize...")
        time.sleep(8)

        # Test browser responsiveness
        try:
            driver.execute_script("return document.readyState")
            logging.info("   ✅ Browser is responsive.")
        except Exception as e:
            logging.error(f"   ❌ Browser not responsive: {e}")
            raise

        logging.info(f"--- 2. Navigating to {START_URL} ---")
        driver.get(START_URL)

        # Handle cookie banner
        try:
            wait = WebDriverWait(driver, 15)
            accept_button = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
            driver.execute_script("arguments[0].click();", accept_button)
            logging.info("   ✅ Cookie banner clicked.")
            time.sleep(3)
        except TimeoutException:
            logging.warning("   ⚠️ Cookie banner not found, continuing.")

        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        logging.info("   ✅ Page is ready.")

        # Main scraping loop
        while len(all_collected_data) < TARGET_COUNT:
            page_count += 1
            logging.info(f"--- Scraping Page {page_count} ---")

            # Step 1: Scrape JSON data
            json_data = scrape_page(driver)
            if not json_data:
                logging.warning("   No JSON-LD data found on this page. Stopping.")
                break

            # Step 2: Scrape icon data using MARKDOWN APPROACH
            icon_data = scrape_page_2(driver)

            # Step 3: Merge the two data sources
            icon_data_map = {item["listing_url"]: item for item in icon_data if item.get("listing_url") != "N/A"}

            merged_page_data = []
            for json_item in json_data:
                listing_url = json_item.get("listing_url")
                if listing_url and listing_url in icon_data_map:
                    json_item.update(icon_data_map[listing_url])
                merged_page_data.append(json_item)

            all_collected_data.extend(merged_page_data)
            logging.info(f"   Collected {len(all_collected_data)}/{TARGET_COUNT} total listings.")

            if len(all_collected_data) >= TARGET_COUNT:
                logging.info("   Target reached!")
                break

            if not navigate_to_next_page(driver):
                break

            pause_duration = random.uniform(3.0, 7.0)
            logging.info(f"   Pausing for {pause_duration:.2f} seconds before next page...")
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
            try:
                driver.quit()
                logging.info("   ✅ Browser closed.")
            except:
                logging.warning("   ⚠️ Browser already closed.")


if __name__ == "__main__":
    run_scraper()