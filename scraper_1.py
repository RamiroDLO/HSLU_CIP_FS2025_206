"""
We are going to implement the following strategy:

Use Selenium to load the page and handle JavaScript rendering.
Wait for the page to load completely, including any dynamic content.
Use container-based scraping to extract data from each car listing.
Extract data from both JSON-LD and the DOM (icons) and merge them.

We have identified that the issue might be due to JavaScript not rendering the icon values immediately.
Therefore, we will add explicit waits and scrolling to trigger lazy loading.
The code below is a fixed version that includes:
Scrolling to trigger lazy loading.
Waiting for icons to be present and have content.
Container-based approach to avoid mixing data between listings."""

"""
FIXED VERSION of AutoScout24 scraper
Strategic fixes applied to resolve N/A values for icons
Enhanced JavaScript rendering handling
"""
"""
ROBUST AutoScout24 Scraper
Fixed version with comprehensive error handling and multiple fallback strategies
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

# Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log', mode='w'),
        logging.StreamHandler()
    ]
)

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


def scrape_page_json(driver) -> List[Dict]:
    """Extracts all listing data from the current page's structured JSON data."""
    listings_data = []

    try:
        logging.info("Looking for structured JSON data on the page...")
        wait = WebDriverWait(driver, 20)
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
                logging.warning(f"Could not parse one item in the JSON data: {e}")
                continue

        logging.info(f"Successfully extracted {len(listings_data)} listings from JSON.")

    except TimeoutException:
        logging.error("Timeout: Could not find the structured JSON data on the page.")
    except Exception as e:
        logging.error(f"Error processing JSON data: {e}")

    return listings_data


def scrape_page_icons(driver) -> List[Dict]:
    """
    Enhanced icon scraping with multiple fallback strategies and better error handling
    """
    results = []

    def extract_icon_value(article_element, icon_titles: list) -> str:
        """Extract value for icons trying multiple possible titles and strategies"""
        for icon_title in icon_titles:
            try:
                # Strategy 1: Direct SVG with title
                svg = article_element.find_element(By.XPATH, f".//svg[.//title[text()='{icon_title}']]")
                p_tag = svg.find_element(By.XPATH, "./following-sibling::p")
                value = p_tag.text.strip()

                if value and value != "-":
                    logging.debug(f"Found '{icon_title}': '{value}'")
                    return value

            except NoSuchElementException:
                continue
            except Exception as e:
                logging.debug(f"Error extracting '{icon_title}': {e}")
                continue

        return "N/A"

    try:
        logging.info("Starting icon data extraction...")

        # Wait for page to be fully ready
        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # Enhanced scrolling to trigger lazy loading
        logging.info("Scrolling to trigger dynamic content...")
        scroll_actions = [
            "window.scrollTo(0, document.body.scrollHeight/3);",
            "window.scrollTo(0, document.body.scrollHeight/2);",
            "window.scrollTo(0, document.body.scrollHeight);",
            "window.scrollTo(0, 0);"
        ]

        for i, action in enumerate(scroll_actions):
            driver.execute_script(action)
            time.sleep(1.5)  # Wait between scrolls

        # Wait for content to stabilize
        time.sleep(3)

        # Find listing containers with multiple fallback selectors
        articles = []
        container_selectors = [
            "article[data-testid='listing-card']",
            "article[data-testid*='listing']",
            "div[data-testid='listing-card']",
            "div[class*='listing-card']",
            "article"
        ]

        for selector in container_selectors:
            articles = driver.find_elements(By.CSS_SELECTOR, selector)
            if articles:
                logging.info(f"Found {len(articles)} containers with selector: {selector}")
                break

        if not articles:
            logging.error("No listing containers found!")
            return []

        # Process each listing
        for idx, article in enumerate(articles):
            listing_data = {
                "listing_url": "N/A",
                "production_date": "N/A",
                "consumption_l_per_100km": "N/A",
                "transmission": "N/A"
            }

            # Extract URL first
            try:
                url_selectors = [
                    ".//a[contains(@href, '/de/d/')]",
                    ".//a[contains(@href, '/angebote/')]",
                    ".//a[@href]"
                ]

                for url_selector in url_selectors:
                    try:
                        link = article.find_element(By.XPATH, url_selector)
                        href = link.get_attribute('href')
                        if href and ('/de/d/' in href or '/angebote/' in href):
                            listing_data["listing_url"] = href.split("?")[0]
                            break
                    except NoSuchElementException:
                        continue
            except Exception as e:
                logging.debug(f"Could not extract URL for listing {idx}: {e}")

            # Define multiple title variations for each icon type
            calendar_titles = ["Calendar icon", "Baujahr", "Year", "Date", "Kalender"]
            consumption_titles = ["Consumption icon", "Verbrauch", "Fuel", "Consumption", "Verbrauch icon"]
            transmission_titles = ["Transmission icon", "Getriebe", "Gear", "Transmission", "Getriebe icon"]

            # Extract icon data
            production_date = extract_icon_value(article, calendar_titles)
            consumption = extract_icon_value(article, consumption_titles)
            transmission = extract_icon_value(article, transmission_titles)

            # Process production date
            if production_date != "N/A":
                # Clean up date format
                listing_data["production_date"] = production_date.split()[0] if production_date else "N/A"

            # Process consumption with better parsing
            if consumption != "N/A":
                # More flexible regex for consumption patterns
                consumption_match = re.search(r'([\d\.,]+)\s*(?:l/100km|L/100km|ℓ/100km|km|l|L)?', consumption,
                                              re.IGNORECASE)
                if consumption_match:
                    try:
                        consumption_value = float(consumption_match.group(1).replace(',', '.'))
                        # Reasonable range for car consumption
                        if 0.5 <= consumption_value <= 30:
                            listing_data["consumption_l_per_100km"] = consumption_value
                    except ValueError:
                        pass

            # Process transmission
            if transmission != "N/A":
                listing_data["transmission"] = _normalize_transmission(transmission)

            results.append(listing_data)

            # Progress logging
            if (idx + 1) % 10 == 0 or (idx + 1) == len(articles):
                logging.info(f"Processed {idx + 1}/{len(articles)} listings")

        # Calculate success statistics
        successful_extractions = {
            'production_date': sum(1 for r in results if r['production_date'] != 'N/A'),
            'consumption': sum(1 for r in results if r['consumption_l_per_100km'] != 'N/A'),
            'transmission': sum(1 for r in results if r['transmission'] != 'N/A'),
            'any_data': sum(1 for r in results if any(v != 'N/A' for v in [
                r['production_date'], r['consumption_l_per_100km'], r['transmission']
            ]))
        }

        logging.info(
            f"Extraction completed: {successful_extractions['any_data']}/{len(results)} listings have icon data")
        logging.info(f"  - Production dates: {successful_extractions['production_date']}/{len(results)}")
        logging.info(f"  - Consumption: {successful_extractions['consumption']}/{len(results)}")
        logging.info(f"  - Transmission: {successful_extractions['transmission']}/{len(results)}")

    except Exception as e:
        logging.error(f"Critical error in icon scraping: {e}", exc_info=True)

    return results


def navigate_to_next_page(driver) -> bool:
    """Navigates to the next page with enhanced waiting."""
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='pagination-next']")
        if next_button and next_button.is_enabled():
            logging.info("Next page button found. Clicking...")
            driver.execute_script("arguments[0].click();", next_button)

            # Wait for page load
            WebDriverWait(driver, 20).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

            # Additional wait for dynamic content
            time.sleep(4)

            # Verify listings are loaded
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "article[data-testid='listing-card']"))
            )

            logging.info("Next page loaded successfully.")
            return True
        else:
            logging.info("Next page button not available.")
            return False

    except NoSuchElementException:
        logging.info("No next page button found.")
        return False
    except Exception as e:
        logging.error(f"Error during pagination: {e}")
        return False


def save_to_csv(data: List[Dict], filename: str):
    """Saves data to CSV with comprehensive statistics."""
    if not data:
        logging.warning("No data to save.")
        return

    logging.info(f"Saving {len(data)} listings to {filename}...")

    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'car_model', 'price_chf', 'mileage', 'engine_power_hp', 'power_mode',
                'production_date', 'consumption_l_per_100km', 'transmission', 'listing_url'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        # Detailed statistics
        stats = {
            'total': len(data),
            'with_production_date': sum(1 for d in data if d.get('production_date') != 'N/A'),
            'with_consumption': sum(1 for d in data if d.get('consumption_l_per_100km') != 'N/A'),
            'with_transmission': sum(1 for d in data if d.get('transmission') != 'N/A'),
            'with_any_icon': sum(1 for d in data if any(
                d.get(field) != 'N/A' for field in ['production_date', 'consumption_l_per_100km', 'transmission']
            ))
        }

        logging.info("✅ Data saved successfully!")
        logging.info("📊 Final Statistics:")
        logging.info(f"   Total listings: {stats['total']}")
        logging.info(
            f"   With any icon data: {stats['with_any_icon']} ({stats['with_any_icon'] / stats['total'] * 100:.1f}%)")
        logging.info(
            f"   With production date: {stats['with_production_date']} ({stats['with_production_date'] / stats['total'] * 100:.1f}%)")
        logging.info(
            f"   With consumption: {stats['with_consumption']} ({stats['with_consumption'] / stats['total'] * 100:.1f}%)")
        logging.info(
            f"   With transmission: {stats['with_transmission']} ({stats['with_transmission'] / stats['total'] * 100:.1f}%)")

    except Exception as e:
        logging.error(f"Failed to save CSV: {e}")


def run_scraper():
    """Main scraping orchestration function."""
    all_collected_data = []
    page_count = 0
    driver = None

    try:
        logging.info("🚀 Starting AutoScout24 Scraper")

        # Browser setup
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")

        driver = uc.Chrome(options=options)
        logging.info("✅ Browser initialized")

        # Navigate to start URL
        logging.info(f"🌐 Navigating to {START_URL}")
        driver.get(START_URL)

        # Handle cookies
        try:
            cookie_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            driver.execute_script("arguments[0].click();", cookie_button)
            logging.info("✅ Cookies accepted")
            time.sleep(2)
        except TimeoutException:
            logging.info("ℹ️ No cookie banner found")

        # Main scraping loop
        while len(all_collected_data) < TARGET_COUNT:
            page_count += 1
            logging.info(f"📄 Processing page {page_count}")

            # Wait for page readiness
            WebDriverWait(driver, 20).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(2)

            # Scrape data from both sources
            json_data = scrape_page_json(driver)
            if not json_data:
                logging.warning("No JSON data found - stopping")
                break

            icon_data = scrape_page_icons(driver)

            # Merge data
            icon_map = {item["listing_url"]: item for item in icon_data if item.get("listing_url") != "N/A"}
            merged_data = []

            for json_item in json_data:
                listing_url = json_item.get("listing_url")
                if listing_url and listing_url in icon_map:
                    json_item.update(icon_map[listing_url])
                merged_data.append(json_item)

            all_collected_data.extend(merged_data)
            logging.info(f"📊 Total collected: {len(all_collected_data)}/{TARGET_COUNT}")

            # Check target
            if len(all_collected_data) >= TARGET_COUNT:
                logging.info("🎯 Target reached!")
                break

            # Pagination
            if not navigate_to_next_page(driver):
                logging.info("⏹️ No more pages available")
                break

            # Random delay between pages
            delay = random.uniform(2, 5)
            logging.info(f"⏳ Waiting {delay:.1f}s before next page...")
            time.sleep(delay)

    except KeyboardInterrupt:
        logging.info("⏹️ Scraping interrupted by user")
    except Exception as e:
        logging.error(f"💥 Fatal error: {e}", exc_info=True)
    finally:
        # Save results
        if all_collected_data:
            save_to_csv(all_collected_data, OUTPUT_FILENAME)

        # Cleanup
        if driver:
            driver.quit()
            logging.info("✅ Browser closed")

        logging.info("🏁 Scraping completed")


if __name__ == "__main__":
    run_scraper()