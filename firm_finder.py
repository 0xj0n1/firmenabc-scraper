
#!/usr/bin/env python3
"""
Firm Finder - A script to find companies without websites on Firmenabc.at
Focuses on coaches, therapists, and similar professions.
"""

import argparse
import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

import requests
from bs4 import BeautifulSoup
import schedule

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('firm_finder.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://www.firmenabc.at"
SEARCH_URL = f"{BASE_URL}/suche/ergebnisse"
RESULTS_PER_RUN = 12
DATA_DIR = Path("data")
CONTACTED_FILE = DATA_DIR / "contacted.json"

# Search keywords for relevant professions
KEYWORDS = [
    "Coach", "Coaching", "Therapeut", "Therapie", "Psychotherapeut", 
    "Lebensberatung", "Mentaltraining", "Persönlichkeitsentwicklung",
    "Beratung", "Berater", "Trainer", "Training", "Supervision",
    "Psychologe", "Psychologie", "Gesundheitscoach", "Businesscoach"
]

class FirmFinder:
    def __init__(self):
        """Initialize the FirmFinder class."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
        })
        
        # Create data directory if it doesn't exist
        DATA_DIR.mkdir(exist_ok=True)
        
        # Load previously contacted companies
        self.contacted_companies = self._load_contacted_companies()
        
    def _load_contacted_companies(self) -> Set[str]:
        """Load the set of previously contacted company IDs."""
        if CONTACTED_FILE.exists():
            try:
                with open(CONTACTED_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data.get("contacted_ids", []))
            except json.JSONDecodeError:
                logger.error(f"Error parsing {CONTACTED_FILE}. Starting with empty set.")
                return set()
        return set()
    
    def _save_contacted_companies(self):
        """Save the set of contacted company IDs."""
        with open(CONTACTED_FILE, 'w', encoding='utf-8') as f:
            json.dump({"contacted_ids": list(self.contacted_companies)}, f, ensure_ascii=False, indent=2)
    
    def search_companies(self, keyword: str, page: int = 1) -> List[str]:
        """
        Search for companies using the given keyword and return company profile URLs.
        
        Args:
            keyword: Search term to use
            page: Page number for pagination
            
        Returns:
            List of company profile URLs
        """
        params = {
            "tx_indexedsearch_pi2[search][word]": keyword,
            "page": page
        }
        
        try:
            response = self.session.get(SEARCH_URL, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            company_links = []
            
            # Find all company links in search results
            for link in soup.select('a.company-name'):
                href = link.get('href')
                if href and href.startswith('/'):
                    company_links.append(f"{BASE_URL}{href}")
            
            return company_links
        
        except requests.RequestException as e:
            logger.error(f"Error searching for '{keyword}' on page {page}: {e}")
            return []
    
    def extract_company_id(self, url: str) -> Optional[str]:
        """Extract the unique company ID from a company profile URL."""
        match = re.search(r'_([A-Za-z0-9]+)$', url)
        return match.group(1) if match else None
    
    def check_company_has_website(self, url: str) -> bool:
        """
        Check if a company has a website listed in their profile.
        
        Args:
            url: Company profile URL
            
        Returns:
            True if the company has a website, False otherwise
        """
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for contact information section
            contact_section = soup.select_one('.contact-info')
            if not contact_section:
                return False
            
            # Check if there's a website entry (W:)
            website_entry = contact_section.find(string=lambda text: text and text.strip().startswith('W:'))
            return bool(website_entry)
            
        except requests.RequestException as e:
            logger.error(f"Error checking company website at {url}: {e}")
            return False
    
    def extract_company_info(self, url: str) -> Optional[Dict]:
        """
        Extract company information from their profile page.
        
        Args:
            url: Company profile URL
            
        Returns:
            Dictionary with company information or None if extraction failed
        """
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            company_id = self.extract_company_id(url)
            
            if not company_id:
                return None
            
            # Extract company name
            name_elem = soup.select_one('h1.company-name')
            name = name_elem.text.strip() if name_elem else "Unknown"
            
            # Extract contact information
            contact_section = soup.select_one('.contact-info')
            address = ""
            phone = ""
            email = ""
            
            if contact_section:
                # Extract address
                address_elem = contact_section.select_one('.address')
                if address_elem:
                    address = ' '.join([line.strip() for line in address_elem.stripped_strings])
                
                # Extract phone (T:)
                phone_elem = contact_section.find(string=lambda text: text and text.strip().startswith('T:'))
                if phone_elem:
                    phone = phone_elem.strip()[2:].strip()
                
                # Extract email using mailto links
                email_link = contact_section.select_one('a[href^="mailto:"]')
                if email_link:
                    email = email_link.get('href')[7:]  # Remove 'mailto:' prefix
            
            # Extract description/about text
            description = ""
            description_elem = soup.select_one('.company-description')
            if description_elem:
                description = description_elem.text.strip()
            
            # Extract industry/category
            category = ""
            category_elem = soup.select_one('.company-category')
            if category_elem:
                category = category_elem.text.strip()
            
            return {
                "id": company_id,
                "url": url,
                "name": name,
                "address": address,
                "phone": phone,
                "email": email,
                "description": description,
                "category": category,
                "found_date": datetime.now().strftime("%Y-%m-%d")
            }
            
        except requests.RequestException as e:
            logger.error(f"Error extracting company info from {url}: {e}")
            return None
    
    def find_companies_without_websites(self, limit: int = RESULTS_PER_RUN) -> List[Dict]:
        """
        Find companies without websites based on search keywords.
        
        Args:
            limit: Maximum number of companies to find
            
        Returns:
            List of company information dictionaries
        """
        companies_found = []
        
        for keyword in KEYWORDS:
            if len(companies_found) >= limit:
                break
                
            logger.info(f"Searching for '{keyword}'...")
            page = 1
            max_pages = 5  # Limit to prevent excessive requests
            
            while len(companies_found) < limit and page <= max_pages:
                company_urls = self.search_companies(keyword, page)
                
                if not company_urls:
                    break
                    
                for url in company_urls:
                    company_id = self.extract_company_id(url)
                    
                    # Skip if already contacted or no valid ID
                    if not company_id or company_id in self.contacted_companies:
                        continue
                    
                    # Check if company has a website
                    if not self.check_company_has_website(url):
                        company_info = self.extract_company_info(url)
                        
                        if company_info:
                            companies_found.append(company_info)
                            self.contacted_companies.add(company_id)
                            logger.info(f"Found company without website: {company_info['name']}")
                            
                            # Add a small delay to avoid overloading the server
                            time.sleep(1)
                    
                    if len(companies_found) >= limit:
                        break
                
                page += 1
                time.sleep(2)  # Delay between page requests
        
        return companies_found
    
    def save_results(self, companies: List[Dict]):
        """
        Save the found companies to a JSON file.
        
        Args:
            companies: List of company information dictionaries
        """
        if not companies:
            logger.info("No new companies found to save.")
            return
            
        # Create filename with current date
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = DATA_DIR / f"{date_str}_firms.json"
        
        # Save companies to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(companies, f, ensure_ascii=False, indent=2)
            
        # Update contacted companies file
        self._save_contacted_companies()
        
        logger.info(f"Saved {len(companies)} companies to {filename}")
    
    def run(self):
        """Run the company finder process."""
        logger.info("Starting company finder process...")
        
        try:
            companies = self.find_companies_without_websites()
            self.save_results(companies)
            logger.info(f"Found and saved {len(companies)} companies without websites.")
        except Exception as e:
            logger.error(f"Error in company finder process: {e}")
            
        logger.info("Company finder process completed.")

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description="Find companies without websites on Firmenabc.at")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()
    
    finder = FirmFinder()
    
    if args.once:
        # Run once and exit
        finder.run()
    else:
        # Schedule daily run at 8:00 AM
        schedule.every().day.at("08:00").do(finder.run)
        logger.info("Scheduled daily run at 08:00. Press Ctrl+C to exit.")
        
        # Run immediately on startup
        finder.run()
        
        # Keep running until interrupted
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Process interrupted by user.")

if __name__ == "__main__":
    main()
