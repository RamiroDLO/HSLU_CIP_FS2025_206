"""
Orchestrator for the web scraping process.
Manages the browser and coordinates the scraper.
"""
import time
import logging
import random

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from browser_scraper import BrowserScraper
from autoscout_selenium_scraper import AutoScoutScraper

logger = logging.getLogger(__name__)

class WebScraperOrchestrator:
    def __init__(self, headless: bool = False, rate_limit: float = 3.0):
        self.browser = BrowserScraper(headless=headless)
        self.scraper = AutoScoutScraper()
        self.rate_limit = rate_limit
        self.collected_data = []

    def random_micro_pause(self):
        """A short, random pause to mimic human reading time."""
        delay = random.uniform(1.0, 3.0)
        logger.debug(f"Micro pause: {delay:.2f} seconds...")
        time.sleep(delay)

    def wait_for_rate_limit(self):
        """Implements rate limiting with a random, human-like delay."""
        delay = random.uniform(5.0, 12.0)  # Increased and varied the delay range
        logger.info(f"Rate limiting: waiting {delay:.2f} seconds...")
        time.sleep(delay)

    def run(self, target_count: int, filename: str):
        """Main method to run the scraping process."""
        try:
            self.browser.setup_driver()
            start_url = "https://www.autoscout24.ch/de/autos/alle-marken"
            self.browser.navigate_to_page(start_url)

            # --- HANDLE COOKIE BANNER ---
            try:
                logger.info("Checking for cookie consent banner...")
                wait = WebDriverWait(self.browser.get_driver(), 10)

                # CORRECTED CODE BLOCK:
                accept_button = wait.until(
                    EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
                )
                # Use the more reliable JavaScript click
                self.browser.get_driver().execute_script("arguments[0].click();", accept_button)
                logger.info("Cookie consent banner accepted.")
                time.sleep(2)
            except TimeoutException:
                logger.info("Cookie consent banner not found, continuing...")
            # --- END OF COOKIE LOGIC ---
            self.browser.move_mouse_to_neutral_location()
            # --- NEW: Add an explicit wait for the page to be ready after cookie click ---
            try:
                logger.info("Waiting for page to become interactive after cookie consent...")
                WebDriverWait(self.browser.get_driver(), 15).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
                logger.info("Page is ready. Starting main scraping loop.")
            except TimeoutException:
                logger.error("Page did not become ready after cookie consent. The script may hang or fail.")
            page_count = 0

            try:
                while len(self.collected_data) < target_count:
                    page_count += 1
                    logger.info(
                        f"Scraping page {page_count} (collected {len(self.collected_data)}/{target_count} listings)")

                    # Check for CAPTCHA
                    if self.browser.check_for_captcha():
                        self.browser.handle_captcha_prompt()

                    # Extract listings from current page
                    try:
                        page_listings = self.scraper.get_listings_on_page(self.browser.get_driver())
                        self.collected_data.extend(page_listings)
                        logger.info(f"Page {page_count}: Extracted {len(page_listings)} new listings.")

                        # Check if target is reached after adding new listings
                        if len(self.collected_data) >= target_count:
                            logger.info(f"Target of {target_count} listings reached!")
                            break

                        # Use a micro-pause before navigating
                        self.random_micro_pause()

                        # Navigate to next page
                        if not self.scraper.navigate_to_next_page(self.browser.get_driver()):
                            logger.info("No more pages available.")
                            break

                        # Rate limiting between pages
                        self.wait_for_rate_limit()

                    except TimeoutException as e:
                        logger.error(f"Timeout on page {page_count}: {e}. Skipping to next page...")
                        # Try to continue to next page if possible
                        if not self.scraper.navigate_to_next_page(self.browser.get_driver()):
                            logger.info("No more pages available after timeout.")
                            break
                        continue
                    except Exception as e:
                        logger.error(f"Unexpected error on page {page_count}: {e}. Attempting to continue...")
                        # Try to continue to next page if possible
                        if not self.scraper.navigate_to_next_page(self.browser.get_driver()):
                            logger.info("No more pages available after error.")
                            break
                        continue

            except KeyboardInterrupt:
                logger.info("Scraping interrupted by user. Saving collected data...")
            except Exception as e:
                logger.error(f"Fatal error during scraping: {e}")

            finally:
                # This ensures data is saved even if there's an error or interrupt
                self.scraper.save_data_to_csv(self.collected_data, filename)
                logger.info(f"Scraping ended. Collected {len(self.collected_data)} listings across {page_count} pages.")

        except Exception as e:
            logger.error(f"Failed to initialize scraping session: {e}")
            raise

    def close(self):
        """Closes the browser."""
        self.browser.close_driver()