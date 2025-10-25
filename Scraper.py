"""
AutoScout24.ch Web Scraper - Structure-Aware Extraction
Uses SVG icon titles + sibling <p> tags with fallback to regex
MODIFIED: Scrapes only 4 listings per page then moves to next page
"""
import time
import json
import csv
import random
import logging
import re
import undetected_chromedriver as uc
from typing import List, Dict, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

# Configuration
TARGET_COUNT = 2000  # Total listings to scrape
LISTINGS_PER_PAGE = 4  # ← NEW: Only scrape 4 listings per page
OUTPUT_FILENAME = "autoscout_data_complete.csv"
START_URL = "https://www.autoscout24.ch/de/autos/alle-marken"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper_final.log', mode='w'),
        logging.StreamHandler()
    ]
)


def extract_power_mode(fuel_type_text: str) -> str:
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


def normalize_transmission(raw: str) -> str:
    if not raw or raw == "-" or raw == "—":
        return "N/A"
    txt = raw.strip().lower()
    if any(k in txt for k in ("halbautomatisches getriebe", "halbautomatik")):
        return "Halbautomatik"
    if any(k in txt for k in ("automat", "automatic", "automatik", "automatisches getriebe")):
        return "Automat"
    if any(k in txt for k in ("manuell", "manual", "schalt", "schaltgetriebe")):
        return "Manuell"
    return raw.strip()[:20]


def extract_value_by_icon(article, icon_title: str) -> Optional[str]:
    """
    Extract value by finding SVG icon and getting sibling <p> tag
    Manually iterates through titles to handle newlines/whitespace
    """
    try:
        # Extract keyword from icon title (e.g., "Calendar" from "Calendar icon")
        key_word = icon_title.split()[0].lower()

        # Find all title tags and manually check each one
        all_titles = article.find_all('title')
        title_tag = None

        for title in all_titles:
            if title.string:
                # Strip whitespace and check if keyword is in the text
                cleaned_text = title.string.strip().lower()
                if key_word in cleaned_text:
                    title_tag = title
                    break

        if not title_tag:
            return None

        # Navigate to parent SVG
        svg = title_tag.find_parent('svg')
        if not svg:
            return None

        # Look for sibling <p> tag with class containing "chakra-text"
        p_tag = svg.find_next_sibling('p', class_=lambda x: x and 'chakra-text' in x)

        if p_tag:
            text = p_tag.get_text(strip=True)
            if text in ['-', '—', '–', '']:
                return None
            return text

        # Fallback: look in parent container
        parent = svg.find_parent('div')
        if parent:
            p_tag = parent.find('p', class_=lambda x: x and 'chakra-text' in x)
            if p_tag:
                text = p_tag.get_text(strip=True)
                if text in ['-', '—', '–', '']:
                    return None
                return text

    except Exception as e:
        pass

    return None


def scrape_json_data(driver) -> List[Dict]:
    listings_data = []
    try:
        logging.info("   Extracting JSON-LD data...")
        wait = WebDriverWait(driver, 15)
        script_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "script[data-testid='structured-schema-srp']"))
        )
        json_text = script_element.get_attribute('innerHTML')
        structured_data = json.loads(json_text)

        car_list = structured_data.get('mainEntity', {}).get('offers', {}).get('itemListElement', [])

        # ← MODIFIED: Only take first 4 listings
        for item in car_list[:LISTINGS_PER_PAGE]:
            try:
                offers = item.get('offers', {})
                item_offered = offers.get('itemOffered', {})
                vehicle_engine = item_offered.get('vehicleEngine', {})

                listing_url = item.get('url') or item.get('@id') or offers.get('url') or item_offered.get('url')
                if listing_url:
                    listing_url = listing_url.split("?")[0]

                data = {
                    'car_model': item.get('name', 'N/A'),
                    'price_chf': offers.get('price', 'N/A'),
                    'mileage': item_offered.get('mileageFromOdometer', {}).get('value', 'N/A'),
                    'engine_power_hp': vehicle_engine.get('enginePower', {}).get('value', 'N/A'),
                    'power_mode': extract_power_mode(vehicle_engine.get('fuelType', 'N/A')),
                    'listing_url': listing_url if listing_url else 'N/A'
                }
                listings_data.append(data)
            except Exception as e:
                logging.warning(f"   Could not parse JSON item: {e}")

        logging.info(f"   ✅ Extracted {len(listings_data)} from JSON-LD (limited to {LISTINGS_PER_PAGE})")
    except Exception as e:
        logging.error(f"   ❌ JSON extraction error: {e}")

    return listings_data


def scrape_html_hybrid_approach(driver) -> List[Dict]:
    """
    Hybrid extraction: Structure-aware with regex fallback
    Primary: Use SVG icon + sibling <p> tag
    Fallback: Regex on article text
    MODIFIED: Only scrape first 4 listings
    """
    results = []

    try:
        logging.info("   Getting page source...")
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # METHOD 1: Find car listings by their <li class="css-0"> containers (excludes ads)
        car_list_items = soup.find_all('li', class_='css-0')
        articles = [li.find('article') for li in car_list_items if li.find('article')]

        # METHOD 2 (Fallback): If METHOD 1 fails, use data-testid
        if not articles:
            logging.info("   Method 1 failed, trying data-testid method...")
            listing_links = soup.find_all('a', attrs={'data-testid': re.compile(r'listing-card-\d+')})
            articles = [link.find_parent('article') for link in listing_links if link.find_parent('article')]

        # METHOD 3 (Last resort): Find all articles
        if not articles:
            logging.info("   Method 2 failed, using all articles...")
            articles = soup.find_all('article')

        # ← MODIFIED: Only process first 4 articles
        articles = articles[:LISTINGS_PER_PAGE]

        logging.info(f"   Found {len(articles)} car articles (limited to {LISTINGS_PER_PAGE} per page)")

        if not articles:
            return []

        # Save first 5 articles for debugging to compare structures
        try:
            for i in range(min(5, len(articles))):
                with open(f'DEBUG_article_{i+1}.html', 'w', encoding='utf-8') as f:
                    f.write(str(articles[i].prettify()))

            logging.info(f"   💾 Saved first {min(5, len(articles))} articles as DEBUG_article_N.html")

            # Debug: Check what icons are present in first 3 articles
            for i in range(min(3, len(articles))):
                icons_found = articles[i].find_all('title')
                icon_list = [icon.string.strip() if icon.string else 'None' for icon in icons_found]
                logging.info(f"   🔍 Article {i+1} icons: {icon_list}")

        except Exception as e:
            logging.warning(f"   Could not save debug files: {e}")

        # Define known transmission types for fallback
        TRANSMISSION_PATTERNS = [
            'Automatik',
            'Automat',
            'Automatisches Getriebe',
            'Manuell',
            'Manuelles Getriebe',
            'Schaltgetriebe',
            'Halbautomatik',
            'Halbautomatisches Getriebe'
        ]

        for idx, article in enumerate(articles):
            data = {
                'production_date': 'N/A',
                'consumption_l_per_100km': 'N/A',
                'transmission': 'N/A',
                'listing_url': 'N/A'
            }

            try:
                # Get listing URL
                link_tag = article.find('a', href=True)
                if link_tag:
                    full_url = link_tag['href']
                    if full_url.startswith('http'):
                        data['listing_url'] = full_url.split("?")[0]
                    elif full_url.startswith('/'):
                        data['listing_url'] = f"https://www.autoscout24.ch{full_url.split('?')[0]}"

                # Extract with structure-aware method
                production_date = extract_value_by_icon(article, "Calendar icon")
                if production_date:
                    data['production_date'] = production_date

                consumption = extract_value_by_icon(article, "Fuel icon")
                if consumption:
                    data['consumption_l_per_100km'] = consumption

                transmission = extract_value_by_icon(article, "Transmission icon")
                if transmission:
                    data['transmission'] = normalize_transmission(transmission)

                # FALLBACK: Regex extraction if structure-aware failed
                article_text = article.get_text(separator=' ', strip=True)

                # Fallback: Production Date (e.g., "10/2023", "2023")
                if data['production_date'] == 'N/A':
                    date_match = re.search(r'\b(\d{1,2}/\d{4}|\d{4})\b', article_text)
                    if date_match:
                        data['production_date'] = date_match.group(1)

                # Fallback: Consumption (e.g., "5.2 l/100 km")
                if data['consumption_l_per_100km'] == 'N/A':
                    cons_match = re.search(r'(\d+\.\d+)\s*l/100\s*km', article_text)
                    if cons_match:
                        data['consumption_l_per_100km'] = cons_match.group(1)

                # Fallback: Transmission
                if data['transmission'] == 'N/A':
                    for pattern in TRANSMISSION_PATTERNS:
                        if pattern in article_text:
                            data['transmission'] = normalize_transmission(pattern)
                            break

                results.append(data)

            except Exception as e:
                logging.warning(f"   Error parsing article {idx + 1}: {e}")
                results.append(data)

        # Log extraction statistics
        stats = {
            'date': sum(1 for r in results if r["production_date"] != "N/A"),
            'trans': sum(1 for r in results if r["transmission"] != "N/A"),
            'cons': sum(1 for r in results if r["consumption_l_per_100km"] != "N/A")
        }

        logging.info(f"   📊 Extraction: Date={stats['date']}/{len(results)}, Trans={stats['trans']}/{len(results)}, Cons={stats['cons']}/{len(results)}")

    except Exception as e:
        logging.error(f"   ❌ Scraping error: {e}", exc_info=True)

    return results


def merge_data(json_data: List[Dict], html_data: List[Dict]) -> List[Dict]:
    html_map = {item["listing_url"]: item for item in html_data if item.get("listing_url") != "N/A"}

    merged = []
    for idx, json_item in enumerate(json_data):
        listing_url = json_item.get('listing_url')
        html_item = html_map.get(listing_url)

        if not html_item and idx < len(html_data):
            html_item = html_data[idx]

        if html_item:
            json_item['production_date'] = html_item.get('production_date', 'N/A')
            json_item['consumption_l_per_100km'] = html_item.get('consumption_l_per_100km', 'N/A')
            json_item['transmission'] = html_item.get('transmission', 'N/A')
        else:
            json_item['production_date'] = 'N/A'
            json_item['consumption_l_per_100km'] = 'N/A'
            json_item['transmission'] = 'N/A'

        merged.append(json_item)

    return merged


def navigate_to_next_page(driver) -> bool:
    try:
        logging.info("   Looking for next page button...")

        # CRITICAL: Scroll to the very bottom to reveal pagination
        logging.info("   Scrolling to bottom to reveal pagination...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # The correct selector from inspect: button[aria-label="next page"]
        selectors = [
            'button[aria-label="next page"]',  # ← THE CORRECT ONE!
            'button[aria-label="previous page"]',  # For reference
            "[data-testid='pagination-next']",
            "button[aria-label*='next']",
            "button[aria-label*='Next']",
            ".pagination button:last-child",
        ]

        next_button = None
        used_selector = None

        for selector in selectors:
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, selector)
                if next_button:
                    used_selector = selector
                    logging.info(f"   ✅ Found next button with selector: {selector}")
                    break
            except:
                continue

        if not next_button:
            logging.error("   ❌ Could not find next button with any selector")
            return False

        # Check if button is disabled
        is_disabled = next_button.get_attribute('disabled')
        aria_disabled = next_button.get_attribute('aria-disabled')
        class_name = next_button.get_attribute('class') or ''

        if is_disabled or aria_disabled == 'true' or 'disabled' in class_name.lower():
            logging.info("   ℹ️  Next button is disabled - reached last page")
            return False

        if next_button.is_enabled():
            logging.info("   ✅ Next button is enabled, clicking...")

            # Scroll to button
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
            time.sleep(1)

            # Click with JavaScript
            driver.execute_script("arguments[0].click();", next_button)
            logging.info("   ✅ Clicked next button")

            time.sleep(3)

            # Wait for page to load
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(2)

            logging.info("   ✅ Successfully navigated to next page")
            return True

        logging.warning("   ⚠️  Next button found but not enabled")
        return False

    except Exception as e:
        logging.error(f"   ❌ Navigation error: {str(e)[:200]}")
        return False


def save_to_csv(data: List[Dict], filename: str):
    if not data:
        return

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'car_model', 'price_chf', 'mileage', 'engine_power_hp', 'power_mode',
            'production_date', 'consumption_l_per_100km', 'transmission', 'listing_url'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    total = len(data)
    stats = {
        'production_date': sum(1 for d in data if d.get('production_date') != 'N/A'),
        'consumption': sum(1 for d in data if d.get('consumption_l_per_100km') != 'N/A'),
        'transmission': sum(1 for d in data if d.get('transmission') != 'N/A')
    }

    logging.info(f"   ✅ Saved {total} listings")
    logging.info(f"   📊 Final Stats:")
    logging.info(f"      - Date: {stats['production_date']}/{total} ({stats['production_date']/total*100:.1f}%)")
    logging.info(f"      - Trans: {stats['transmission']}/{total} ({stats['transmission']/total*100:.1f}%)")
    logging.info(f"      - Cons: {stats['consumption']}/{total} ({stats['consumption']/total*100:.1f}%)")


def run_scraper():
    all_data = []
    page_count = 0
    driver = None

    try:
        logging.info("=== STARTING SCRAPER ===")
        logging.info(f"📋 Configuration: {LISTINGS_PER_PAGE} listings per page, Target: {TARGET_COUNT} total")

        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = uc.Chrome(options=options)
        logging.info("✅ Browser started")

        driver.get(START_URL)

        try:
            wait = WebDriverWait(driver, 15)
            accept_button = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
            driver.execute_script("arguments[0].click();", accept_button)
            time.sleep(3)
        except:
            pass

        WebDriverWait(driver, 15).until(lambda d: d.execute_script("return document.readyState") == "complete")

        while len(all_data) < TARGET_COUNT:
            page_count += 1
            logging.info(f"\n=== PAGE {page_count} ===")

            # Aggressive scrolling to trigger lazy loading
            total_height = driver.execute_script("return document.body.scrollHeight")

            # Scroll down in smaller increments
            for i in range(5):
                scroll_pos = (total_height / 5) * (i + 1)
                driver.execute_script(f"window.scrollTo(0, {scroll_pos});")
                time.sleep(1)  # Wait for content to load

            # Scroll back to top
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)

            # Scroll down again to middle to ensure everything is visible
            driver.execute_script(f"window.scrollTo(0, {total_height / 2});")
            time.sleep(2)

            json_data = scrape_json_data(driver)
            if not json_data:
                break

            time.sleep(3)
            # Using hybrid approach with structure-aware + regex fallback
            html_data = scrape_html_hybrid_approach(driver)

            merged = merge_data(json_data, html_data)
            all_data.extend(merged)

            logging.info(f"📊 Total collected: {len(all_data)}/{TARGET_COUNT}")

            if len(all_data) >= TARGET_COUNT:
                logging.info(f"✅ Reached target of {TARGET_COUNT} listings")
                break

            logging.info("🔄 Navigating to next page...")
            if not navigate_to_next_page(driver):
                logging.warning("❌ Could not navigate to next page - stopping")
                break

            time.sleep(random.uniform(3, 7))

    except Exception as e:
        logging.critical(f"❌ Fatal error: {e}", exc_info=True)
    finally:
        if all_data:
            save_to_csv(all_data, OUTPUT_FILENAME)
        if driver:
            driver.quit()


if __name__ == "__main__":
    run_scraper()