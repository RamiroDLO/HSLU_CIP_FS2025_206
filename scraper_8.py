"""
AutoScout24.ch Web Scraper - DOM Navigation Approach
Uses BeautifulSoup to navigate HTML structure directly
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
from bs4 import BeautifulSoup

# Configuration
TARGET_COUNT = 30
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
    if not raw or raw == "-":
        return "N/A"
    txt = raw.strip().lower()
    if any(k in txt for k in ("halbautomatisches getriebe", "halbautomatik")):
        return "Halbautomatik"
    if any(k in txt for k in ("automat", "automatic", "automatik", "automatisches getriebe")):
        return "Automat"
    if any(k in txt for k in ("manuell", "manual", "schalt", "schaltgetriebe")):
        return "Manuell"
    return raw.strip()[:20]


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

        for item in car_list:
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

        logging.info(f"   ✅ Extracted {len(listings_data)} from JSON-LD")
    except Exception as e:
        logging.error(f"   ❌ JSON extraction error: {e}")

    return listings_data


def scrape_html_selenium_dom(driver) -> List[Dict]:
    """Uses Selenium to find elements in the live DOM (not static HTML)"""
    results = []

    try:
        logging.info("   Finding articles with Selenium...")

        # Find all article elements using Selenium
        articles = driver.find_elements(By.TAG_NAME, "article")
        logging.info(f"   Found {len(articles)} articles via Selenium")

        if not articles:
            return []

        for idx, article in enumerate(articles):
            data = {
                "listing_url": "N/A",
                "production_date": "N/A",
                "consumption_l_per_100km": "N/A",
                "transmission": "N/A"
            }

            # Extract URL
            try:
                link = article.find_element(By.CSS_SELECTOR, "a[href*='/de/d/']")
                href = link.get_attribute('href')
                if href:
                    data["listing_url"] = href.split("?")[0]
            except:
                pass

            # Find Calendar icon using Selenium
            try:
                # Find SVG with title "Calendar icon" within this article
                calendar_svg = article.find_element(By.XPATH, ".//svg[.//title[text()='Calendar icon']]")
                # Get parent div, then find p tag
                parent_div = calendar_svg.find_element(By.XPATH, "./parent::div")
                p_tag = parent_div.find_element(By.TAG_NAME, "p")
                date_text = p_tag.text.strip()

                if 'Neues Fahrzeug' in date_text:
                    data["production_date"] = "Neues Fahrzeug"
                else:
                    date_match = re.search(r'(\d{1,2}\.\d{4})', date_text)
                    if date_match:
                        data["production_date"] = date_match.group(1)

                if idx < 3:
                    logging.info(f"   ✅ Article {idx+1}: Date = '{data['production_date']}'")
            except NoSuchElementException:
                if idx < 3:
                    logging.warning(f"   ❌ Article {idx+1}: Calendar icon not found in DOM")
            except Exception as e:
                if idx < 3:
                    logging.warning(f"   ❌ Article {idx+1}: Date error - {type(e).__name__}: {e}")

            # Find Transmission icon
            try:
                trans_svg = article.find_element(By.XPATH, ".//svg[.//title[text()='Transmission icon']]")
                parent_div = trans_svg.find_element(By.XPATH, "./parent::div")
                p_tag = parent_div.find_element(By.TAG_NAME, "p")
                trans_text = p_tag.text.strip()
                data["transmission"] = normalize_transmission(trans_text)

                if idx < 3:
                    logging.info(f"   ✅ Article {idx+1}: Trans = '{trans_text}'")
            except NoSuchElementException:
                if idx < 3:
                    logging.warning(f"   ❌ Article {idx+1}: Transmission icon not found in DOM")
            except Exception as e:
                if idx < 3:
                    logging.warning(f"   ❌ Article {idx+1}: Trans error - {type(e).__name__}: {e}")

            # Find Consumption icon
            try:
                cons_svg = article.find_element(By.XPATH, ".//svg[.//title[text()='Consumption icon']]")
                parent_div = cons_svg.find_element(By.XPATH, "./parent::div")
                p_tag = parent_div.find_element(By.TAG_NAME, "p")
                cons_text = p_tag.text.strip()

                if cons_text != '-':
                    cons_match = re.search(r'([\d\.,]+)\s*l/100\s*km', cons_text)
                    if cons_match:
                        num_str = cons_match.group(1).replace(',', '.')
                        try:
                            val = float(num_str)
                            if 1 <= val <= 50:
                                data["consumption_l_per_100km"] = val

                                if idx < 3:
                                    logging.info(f"   ✅ Article {idx+1}: Cons = {val}")
                        except:
                            pass
            except Exception as e:
                if idx < 3:
                    logging.debug(f"   ❌ Article {idx+1}: Cons not found - {e}")

            results.append(data)

        # Stats
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
        wait = WebDriverWait(driver, 10)
        next_button = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='pagination-next']"))
        )

        if next_button and next_button.is_enabled():
            driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(2)

            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(3)

            return True
        return False
    except:
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
    logging.info(f"   📊 Final: Date={stats['production_date']}/{total} ({stats['production_date']/total*100:.1f}%), Trans={stats['transmission']}/{total} ({stats['transmission']/total*100:.1f}%)")


def run_scraper():
    all_data = []
    page_count = 0
    driver = None

    try:
        logging.info("=== STARTING SCRAPER ===")

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

            # Aggressive scrolling
            total_height = driver.execute_script("return document.body.scrollHeight")
            for i in range(3):
                scroll_pos = (total_height / 3) * (i + 1)
                driver.execute_script(f"window.scrollTo(0, {scroll_pos});")
                time.sleep(1.5)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)

            json_data = scrape_json_data(driver)
            if not json_data:
                break

            time.sleep(3)
            html_data = scrape_html_selenium_dom(driver)

            merged = merge_data(json_data, html_data)
            all_data.extend(merged)

            logging.info(f"📊 Total: {len(all_data)}/{TARGET_COUNT}")

            if len(all_data) >= TARGET_COUNT:
                break

            if not navigate_to_next_page(driver):
                break

            time.sleep(random.uniform(3, 7))

    except Exception as e:
        logging.critical(f"❌ Fatal: {e}", exc_info=True)
    finally:
        if all_data:
            save_to_csv(all_data, OUTPUT_FILENAME)
        if driver:
            driver.quit()


if __name__ == "__main__":
    run_scraper()