"""
Main execution script for the AutoScout24 scraper.
"""
import logging
from autoscout_orchestrator import WebScraperOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('autoscout_scraper.log'),
        logging.StreamHandler()
    ]
)

if __name__ == "__main__":
    TARGET_LISTINGS = 500
    OUTPUT_FILENAME = "autoscout_data_final.csv"

    # Initialize the orchestrator
    orchestrator = WebScraperOrchestrator(
        headless=False,
        rate_limit=3.0
    )
    
    # Run the scraping process
    try:
        orchestrator.run(
            target_count=TARGET_LISTINGS,
            filename=OUTPUT_FILENAME
        )
    except Exception as e:
        logging.error(f"An unexpected error occurred during execution: {e}")
    finally:
        orchestrator.close()

