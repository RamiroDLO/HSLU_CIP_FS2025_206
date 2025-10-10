import logging
import time
from typing import List, Dict, Optional
from selenium.webdriver.common.action_chains import ActionChains

import undetected_chromedriver as uc  # <-- ADD THIS LINE
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
# Remove these since undetected_chromedriver handles driver management:
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.chrome.service import Service as ChromeService

logger = logging.getLogger(__name__)
logger = logging.getLogger(__name__)

class BrowserScraper:
    def __init__(self, headless: bool = False):
        """Initialize the browser-based scraper"""
        self.driver = None
        self.wait = None

        # Setup Chrome options
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument("--headless")
        
        # Add options to avoid detection and work in sandbox
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--disable-extensions")
        self.chrome_options.add_argument("--disable-plugins")
        # self.chrome_options.add_argument("--disable-images") # Keep images for visual CAPTCHA solving

        self.chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        self.chrome_options.add_argument("--remote-debugging-port=9222")
        # self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # self.chrome_options.add_experimental_option("useAutomationExtension", False)
        self.chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        # Add these to your existing chrome_options
        self.chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        # self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # self.chrome_options.add_experimental_option("useAutomationExtension", False)

        #  adding these for better stealth
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-web-security")
        self.chrome_options.add_argument("--allow-running-insecure-content")
        self.chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        self.chrome_options.add_argument("--disable-background-timer-throttling")
        self.chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        self.chrome_options.add_argument("--disable-renderer-backgrounding")

    import undetected_chromedriver as uc

    def setup_driver(self):
        """Initialize the Chrome WebDriver using undetected-chromedriver"""
        try:
            self.driver = uc.Chrome(options=self.chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            logger.info("Undetected ChromeDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Undetected ChromeDriver: {e}")
            raise

    # Add this new method anywhere inside the BrowserScraper class

    def move_mouse_to_neutral_location(self):
        """Moves the mouse cursor to the body tag to avoid unintended hover effects."""
        try:
            logger.debug("Moving mouse to a neutral location to prevent hover effects...")
            body_element = self.driver.find_element(By.TAG_NAME, "body")
            ActionChains(self.driver).move_to_element(body_element).perform()
        except Exception as e:
            logger.warning(f"Could not move mouse to neutral location: {e}")

    def close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")

    def get_driver(self):
        """Return the WebDriver instance"""
        return self.driver

    def navigate_to_page(self, url: str):
        """Navigate the browser to a given URL with improved waiting"""
        try:
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)

            # Wait for the document to be in a complete state
            WebDriverWait(self.driver, 15).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )

            # Additional wait for a specific element that indicates page readiness
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            logger.info("Successfully loaded page")
        except TimeoutException:
            logger.error("Timeout waiting for page to load")
            raise
        except Exception as e:
            logger.error(f"Error navigating to page: {e}")
            raise

    # In browser_scraper.py, replace the old function with this one

    def check_for_captcha(self) -> bool:
        """Check if CAPTCHA is present with a more targeted and reliable method."""
        try:
            # --- Part 1: Check for specific, reliable technical indicators ---
            # These are unlikely to cause false positives.
            if (self.driver.find_elements(By.ID, "cf-challenge-running") or
                    self.driver.find_elements(By.CSS_SELECTOR, ".h-captcha") or
                    self.driver.find_elements(By.CSS_SELECTOR, ".g-recaptcha")):
                logger.info("CAPTCHA detected by specific technical element (e.g., h-captcha).")
                return True

            # --- Part 2: Check for keywords ONLY in prominent text elements ---
            # This is much safer than searching the entire page source.
            captcha_keywords = ["just a moment", "security check", "verify you are human", "challenge"]

            # We only check important tags like headings where a prompt would be.
            potential_prompt_elements = self.driver.find_elements(By.CSS_SELECTOR, "h1, h2")

            for element in potential_prompt_elements:
                element_text = element.text.lower()
                for keyword in captcha_keywords:
                    if keyword in element_text:
                        logger.info(f"CAPTCHA detected by keyword '{keyword}' in a heading tag.")
                        return True

            # If none of the above were found, it's not a CAPTCHA.
            return False

        except NoSuchElementException:
            return False
        except Exception as e:
            logger.warning(f"Error checking for CAPTCHA: {e}")
            return False

    def handle_captcha_prompt(self):
        """Prompt user to handle CAPTCHA manually"""
        print("\n" + "="*60)
        print("CAPTCHA DETECTED!")
        print("Please solve the CAPTCHA in the browser window.")
        print("After solving, press Enter to continue...")
        print("="*60)
        input()
        logger.info("User indicated CAPTCHA was solved, continuing...")

