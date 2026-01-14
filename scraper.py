import json
import sys
import time
import random
import argparse
import re
from playwright.sync_api import sync_playwright

def random_sleep(min_seconds=1, max_seconds=3):
    time.sleep(random.uniform(min_seconds, max_seconds))

def load_selectors(filepath="selectors.json"):
    with open(filepath, 'r') as f:
        return json.load(f)

def run(query, headless=True, limit=10):
    selectors = load_selectors()
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        
        # Navigate directly to search results
        # This avoids issues with finding the search box
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        page.goto(f"https://www.google.com/maps/search/{encoded_query}")
        random_sleep(2, 4)

        # Handle Cookie Consent if it appears
        try:
            consent_btn = page.query_selector(selectors.get("consent_accept", "form[action*='consent'] button"))
            if consent_btn:
                print("DEBUG: Found consent button, clicking...", file=sys.stderr)
                consent_btn.click()
                random_sleep(2, 4)
        except Exception as e:
            print(f"DEBUG: Consent handling skipped or failed: {e}", file=sys.stderr)
        
        # We don't need to type in search box anymore.

        
        # Wait for results to load
        try:
            page.wait_for_selector(selectors["results_feed"], timeout=15000)
        except:
             # Try to see if we can find results anyway (sometimes feed role differs?)
             print(f"DEBUG: Timeout waiting for results feed. dumping content check...", file=sys.stderr)
             # print(json.dumps({"error": "No results found or timeout."}))
             # return but let's see if we can find cards directly
             pass

        random_sleep(2, 4)

        # Scroll to load more results
        feed_selector = selectors["results_feed"]
        last_count = 0
        try:
            page.hover(feed_selector)
            while True:
                page.mouse.wheel(0, 5000)
                random_sleep(1, 2)
                
                # Check if we've reached the end or simply not loading more
                current_cards = page.query_selector_all(selectors["result_card"])
                current_count = len(current_cards)
                
                # Stop if we have enough cards
                if current_count >= limit:
                    print(f"DEBUG: Reached limit of {limit} cards (found {current_count}). Stopping scroll.", file=sys.stderr)
                    break
                
                if current_count == last_count:
                    # Try one more small scroll/wait to be sure
                    random_sleep(2, 4)
                    current_cards = page.query_selector_all(selectors["result_card"])
                    if len(current_cards) == last_count:
                        print("DEBUG: Reached end of list or stopped loading.", file=sys.stderr)
                        break
                
                last_count = current_count
                print(f"DEBUG: Loaded {last_count} cards so far...", file=sys.stderr)
        except Exception as e:
            print(f"DEBUG: Error during scrolling: {e}", file=sys.stderr)

        # Extract items
        cards = page.query_selector_all(selectors["result_card"])
        print(f"DEBUG: Found {len(cards)} total cards", file=sys.stderr)

        for card in cards:
            data = {}
            try:
                # Click the card to load details
                card.click()
                random_sleep(1.0, 2.5)
                
                # Check for details
                def safe_extract(selector):
                    try:
                        el = page.query_selector(selector)
                        return el.inner_text().strip() if el else None
                    except:
                        return None
                
                def safe_extract_attr(selector, attr):
                    try:
                        el = page.query_selector(selector)
                        return el.get_attribute(attr) if el else None
                    except:
                        return None

                data["name"] = safe_extract(selectors["details"]["name"]) or card.get_attribute("aria-label")
                
                # Get the full text of the details panel for robust extraction
                details_text = ""
                try:
                    main_el = page.query_selector("div[role='main']")
                    if main_el:
                        details_text = main_el.inner_text()
                except:
                    pass
                
                # Rating (keep existing selector if it works, fallback to text)
                rating_raw = safe_extract_attr(selectors["details"]["rating"], "aria-label")
                if rating_raw:
                    data["rating"] = rating_raw.split()[0]
                else:
                    # Fallback
                    match = re.search(r'(\d\.\d) stars', details_text)
                    data["rating"] = match.group(1) if match else None

                # Reviews Count
                # Look for patterns like "(1,234)" or "1,234 reviews"
                import re
                reviews_match = re.search(r'\(([\d,]+)\)', details_text)
                if reviews_match:
                     data["reviews_count"] = reviews_match.group(1).replace(',', '')
                else:
                     # Try "X reviews"
                     reviews_match_2 = re.search(r'([\d,]+) reviews', details_text)
                     if reviews_match_2:
                         data["reviews_count"] = reviews_match_2.group(1).replace(',', '')
                     else:
                         data["reviews_count"] = "0"
                
                data["category"] = safe_extract(selectors["details"]["category"])
                
                data["address"] = safe_extract(selectors["details"]["address"])
                data["website"] = safe_extract_attr(selectors["details"]["website"], "href")
                data["phone"] = safe_extract(selectors["details"]["phone"])
                
                # Open Status
                # Look for "Open" or "Closed" lines in the text
                open_match = re.search(r'(Open|Closed|Closes|Opens) [^\n]*', details_text)
                if open_match:
                    open_text = open_match.group(0)
                    # Split by middle dot (·) or similar characters
                    parts = re.split(r'[·⋅]', open_text)
                    data["open_status"] = parts[0].strip()
                else:
                    data["open_status"] = None

                # Coordinates from URL
                current_url = page.url
                coords = re.search(r'@([-0-9.]+),([-0-9.]+)', current_url)
                if coords:
                    data["latitude"] = float(coords.group(1))
                    data["longitude"] = float(coords.group(2))
                else:
                    data["latitude"] = None
                    data["longitude"] = None
                
                if data["name"]:
                    results.append(data)
                
                if len(results) >= limit:
                    print(f"DEBUG: Reached limit of {limit} results.", file=sys.stderr)
                    break
                
            except Exception as e:
                print(f"Error scraping card: {e}", file=sys.stderr)
                continue
        
        browser.close()

    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Google Maps Scraper")
    parser.add_argument("query", help="Search query (e.g., 'restaurants in NY')")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--no-headless", action="store_false", dest="headless", help="Run in visible mode")
    parser.set_defaults(headless=True)
    
    args = parser.parse_args()
    results = run(args.query, headless=args.headless)
    # Output JSON to stdout
    print(json.dumps(results, indent=2))
