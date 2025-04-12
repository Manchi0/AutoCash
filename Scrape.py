#!/usr/bin/env python3
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# ----- Part 1: Scrape the raw text data from the webpage -----
def get_raw_page_text(url):
    # Set up ChromeDriver options
    chrome_options = Options()
    chrome_options.add_argument("--headless")       # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")

    # Point Selenium to the correct ChromeDriver path
    service = Service('/opt/homebrew/bin/chromedriver')
    
    # Initialize the WebDriver with the service and options
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Open the target URL
    driver.get(url)
    
    # Wait for the page to load (adjust time if needed)
    time.sleep(5)
    
    # Get the fully rendered HTML from the page
    html = driver.page_source
    driver.quit()
    
    # Parse using BeautifulSoup and extract all text
    soup = BeautifulSoup(html, 'html.parser')
    raw_text = soup.get_text(" ", strip=True)
    return raw_text

# ----- Part 2: Clean and extract reward details -----
def clean_reward_data(raw_text):
    # Remove unwanted characters/symbols that tend to clutter the text.
    # You can expand this list as needed.
    cleaned_text = raw_text.replace("¤", " ").replace("‡", " ").replace("♦︎", " ")

    # Instead of splitting by newline (which may not be present),
    # we use a regular expression to locate reward blocks in the text.
    # The pattern below looks for the reward percent followed by "CASH BACK On" 
    # and then captures a block of text (non-greedily) until the next similar reward block
    # or the end of the string.
    # We assume that the category part does not include a digit at the beginning.
    pattern = re.compile(
        r"(?P<percent>\d+)%\s*CASH\s+BACK\s+On\s+(?P<category>[^0-9]+?)(?=\s+\d+%\s*CASH\s+BACK|\Z)",
        re.IGNORECASE | re.DOTALL
    )
    
    # Pattern to capture a spending limit if it appears (e.g., "up to $6,000")
    limit_pattern = re.compile(r"up to \$([\d,]+)", re.IGNORECASE)
    
    extracted_rewards = []
    seen = set()  # To deduplicate similar reward matches.
    
    for match in pattern.finditer(cleaned_text):
        percent = match.group("percent").strip()
        # The category field might have extra punctuation or repeated phrases.
        category_text = match.group("category").strip()
        
        # Attempt to further clean the category text:
        # Replace multiple spaces with a single space.
        category = re.sub(r'\s+', ' ', category_text)
        # Strip off any trailing words that don't look like part of the category
        # (this could be improved with additional logic).
        
        details = match.group(0)  # Full matched reward segment

        # Try to extract a limit if present from the matched segment.
        limit_match = limit_pattern.search(details)
        limit = limit_match.group(1) if limit_match else None

        # Create a key for deduplication (here, combining percent and cleaned category)
        dedup_key = (percent, category)
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        extracted_rewards.append({
            "category": category,
            "reward_percent": percent,
            "limit": limit,
            "full_text": details.strip()
        })
    
    return extracted_rewards

# ----- Part 3: Main workflow -----
def main():
    url = "https://www.americanexpress.com/us/credit-cards/card/blue-cash-everyday/"
    print("Scraping raw text from:", url)
    raw_text = get_raw_page_text(url)
    
    print("\nCleaning and extracting reward details...\n")
    rewards = clean_reward_data(raw_text)
    
    if rewards:
        print("Extracted Rewards:")
        for reward in rewards:
            print(f"Category/Company: {reward['category']}")
            print(f"Reward Percent: {reward['reward_percent']}%")
            if reward["limit"]:
                print(f"Spending Limit: ${reward['limit']}")
            else:
                print("Spending Limit: Not specified")
            print("Full text:", reward["full_text"])
            print("-----")
    else:
        print("No reward data extracted. Check your regex patterns or raw text content.")

if __name__ == "__main__":
    main()
