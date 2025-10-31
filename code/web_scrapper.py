"""
Web scraper for retirement community website.
Extracts daily schedules, menus, and activity information.
Uses Selenium to handle JavaScript-rendered content.
Includes caching mechanism to reduce website load (refreshes every 2 weeks).
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import json
import os
import time
import glob

# Target website URL
web_link = "https://a.mwapp.net/p/mweb_ws.v?id=82352517&c=82352665&n=Main"

# Login credentials (if needed - set via environment variables for security)
LOGIN_USER = os.getenv('RETIREMENT_SITE_USER', '')
LOGIN_PASS = os.getenv('RETIREMENT_SITE_PASS', '')

# Cache settings
CACHE_FILE = os.path.join(os.path.dirname(__file__), 'community_data_cache.json')
CACHE_DURATION_DAYS = 14  # 2 weeks

def scrape_retirement_community_info(url=web_link, timeout=20):
    """
    Scrapes information from the retirement community website using Selenium.
    This allows us to capture JavaScript-rendered content like event listings.
    
    Args:
        url (str): The URL to scrape
        timeout (int): Maximum wait time in seconds
        
    Returns:
        dict: Dictionary containing scraped information
    """
    driver = None
    try:
        # Set up Chrome options for headless browsing
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Initialize the Chrome driver with automatic driver management
        print("  → Initializing browser...")
        try:
            # Try to use webdriver-manager
            driver_path = ChromeDriverManager().install()
            # Ensure we're using the actual chromedriver executable
            if 'THIRD_PARTY' in driver_path or not driver_path.endswith('chromedriver'):
                # Fix the path if it points to the wrong file
                import glob
                driver_dir = os.path.dirname(driver_path)
                # Look for the actual chromedriver executable
                possible_paths = glob.glob(os.path.join(driver_dir, '**/chromedriver'), recursive=True)
                if possible_paths:
                    driver_path = possible_paths[0]
            service = Service(driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            # If webdriver-manager fails, try to use system chromedriver
            print(f"  → Webdriver-manager failed ({str(e)}), trying system chromedriver...")
            try:
                driver = webdriver.Chrome(options=chrome_options)
            except:
                raise Exception(f"Could not initialize Chrome. Please install Chrome and chromedriver. Error: {str(e)}")
        
        # Set page load timeout
        driver.set_page_load_timeout(timeout)
        
        # Navigate to the URL
        print(f"  → Loading {url}...")
        driver.get(url)
        
        # Check if login is required and credentials are provided
        if LOGIN_USER and LOGIN_PASS:
            try:
                print("  → Attempting to log in...")
                # Wait for login form
                time.sleep(2)
                # Try to find and fill login fields (adjust selectors as needed)
                try:
                    user_field = driver.find_element(By.NAME, "userid")  # or By.ID, By.CSS_SELECTOR
                    pass_field = driver.find_element(By.NAME, "password")
                    user_field.send_keys(LOGIN_USER)
                    pass_field.send_keys(LOGIN_PASS)
                    # Submit form
                    pass_field.submit()
                    time.sleep(3)
                    print("  → Logged in successfully")
                except Exception as login_err:
                    print(f"  → Login failed: {str(login_err)}")
            except:
                pass
        
        # Wait for dynamic content to load
        print("  → Waiting for dynamic content to load...")
        try:
            # Wait for body to be present
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Scroll down to trigger lazy-loaded content
            print("  → Scrolling to load dynamic content...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Scroll back up
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # Give JavaScript time to finish loading all content
            time.sleep(3)
            
            print("  → Content loaded")
        except Exception as e:
            print(f"  → Warning: {str(e)}")
            time.sleep(5)
        
        # Get the fully rendered page source
        page_source = driver.page_source
        
        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Extract all text content
        text_content = soup.get_text(separator='\n', strip=True)
        
        # Extract specific sections if they exist
        result = {
            'url': url,
            'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'title': soup.title.string if soup.title else "No title found",
            'full_text': text_content,
            'links': [],
            'headings': [],
            'tables': []
        }
        
        # Extract all links
        for link in soup.find_all('a', href=True):
            link_text = link.get_text(strip=True)
            if link_text:
                result['links'].append({
                    'text': link_text,
                    'href': link['href']
                })
        
        # Extract all headings
        for heading_level in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            for heading in soup.find_all(heading_level):
                heading_text = heading.get_text(strip=True)
                if heading_text:
                    result['headings'].append({
                        'level': heading_level,
                        'text': heading_text
                    })
        
        # Extract tables (often used for schedules/menus)
        for table in soup.find_all('table'):
            table_data = []
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                row_data = [cell.get_text(strip=True) for cell in cells]
                if any(row_data):  # Only add non-empty rows
                    table_data.append(row_data)
            if table_data:
                result['tables'].append(table_data)
        
        return result
        
    except Exception as e:
        error_msg = f'Scraping failed: {str(e)}'
        print(f"  ✗ Error: {error_msg}")
        return {
            'error': error_msg,
            'url': url,
            'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    finally:
        # Always close the browser
        if driver:
            try:
                driver.quit()
                print("  → Browser closed")
            except:
                pass

def format_scraped_content_for_prompt(scraped_data):
    """
    Formats scraped data into a readable string for use in system prompts.
    
    Args:
        scraped_data (dict): Dictionary containing scraped information
        
    Returns:
        str: Formatted text for system prompt
    """
    if 'error' in scraped_data:
        return f"Error retrieving website information: {scraped_data['error']}"
    
    formatted_text = f"""
=== RETIREMENT COMMUNITY INFORMATION ===
Source: {scraped_data['url']}
Last Updated: {scraped_data['scraped_at']}

"""
    
    # Add headings section
    if scraped_data.get('headings'):
        formatted_text += "SECTIONS AVAILABLE:\n"
        for heading in scraped_data['headings'][:10]:  # Limit to first 10 headings
            formatted_text += f"- {heading['text']}\n"
        formatted_text += "\n"
    
    # Add tables (schedules/menus often in tables)
    if scraped_data.get('tables'):
        formatted_text += "SCHEDULE/MENU DATA:\n"
        for i, table in enumerate(scraped_data['tables'][:3], 1):  # Limit to first 3 tables
            formatted_text += f"\nTable {i}:\n"
            for row in table[:10]:  # Limit rows
                formatted_text += " | ".join(row) + "\n"
        formatted_text += "\n"
    
    # Add main content (truncated for token limits)
    if scraped_data.get('full_text'):
        full_text = scraped_data['full_text']
        # Truncate to reasonable length
        max_length = 2000
        if len(full_text) > max_length:
            full_text = full_text[:max_length] + "..."
        formatted_text += f"FULL CONTENT:\n{full_text}\n"
    
    formatted_text += "\n=== END OF COMMUNITY INFORMATION ===\n"
    
    return formatted_text

def load_cache():
    """
    Loads cached data from file if it exists and is recent enough.
    
    Returns:
        dict or None: Cached data if valid, None if cache is invalid or doesn't exist
    """
    try:
        if not os.path.exists(CACHE_FILE):
            return None
        
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        
        # Check if cache is still valid
        cached_time = datetime.strptime(cache['scraped_at'], "%Y-%m-%d %H:%M:%S")
        age = datetime.now() - cached_time
        
        if age.days < CACHE_DURATION_DAYS:
            print(f"✓ Using cached data (age: {age.days} days, {age.seconds // 3600} hours)")
            return cache
        else:
            print(f"✗ Cache expired (age: {age.days} days)")
            return None
            
    except Exception as e:
        print(f"✗ Error loading cache: {e}")
        return None

def save_cache(data):
    """
    Saves scraped data to cache file.
    
    Args:
        data (dict): Scraped data to cache
    """
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✓ Data cached to: {CACHE_FILE}")
    except Exception as e:
        print(f"✗ Error saving cache: {e}")

def clear_cache():
    """
    Deletes the cache file, forcing a fresh scrape on next request.
    """
    try:
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
            print("✓ Cache cleared successfully")
            return True
        else:
            print("✗ No cache file to clear")
            return False
    except Exception as e:
        print(f"✗ Error clearing cache: {e}")
        return False

def get_cached_data(force_refresh=False):
    """
    Gets community data, using cache if available and valid.
    
    Args:
        force_refresh (bool): If True, ignores cache and scrapes fresh data
        
    Returns:
        dict: Scraped community data
    """
    if not force_refresh:
        cached_data = load_cache()
        if cached_data is not None:
            return cached_data
    
    # Cache miss or force refresh - scrape fresh data
    print("⟳ Scraping fresh data from website...")
    scraped_data = scrape_retirement_community_info()
    
    # Only cache if scraping was successful
    if 'error' not in scraped_data:
        save_cache(scraped_data)
    
    return scraped_data

def get_community_context(force_refresh=False):
    """
    Convenience function to get formatted community information with caching.
    
    Args:
        force_refresh (bool): If True, ignores cache and scrapes fresh data
        
    Returns:
        str: Formatted community information for system prompt
    """
    scraped_data = get_cached_data(force_refresh=force_refresh)
    return format_scraped_content_for_prompt(scraped_data)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape retirement community website')
    parser.add_argument('--force-refresh', action='store_true', 
                       help='Force refresh cache, ignoring existing cached data')
    parser.add_argument('--clear-cache', action='store_true',
                       help='Clear the cache and exit')
    args = parser.parse_args()
    
    if args.clear_cache:
        clear_cache()
        exit(0)
    
    # Test the scraper with caching
    print("=" * 60)
    print("RETIREMENT COMMUNITY WEB SCRAPER")
    print("=" * 60)
    print(f"Cache file location: {CACHE_FILE}")
    print(f"Cache duration: {CACHE_DURATION_DAYS} days (2 weeks)")
    print("=" * 60)
    print()
    
    data = get_cached_data(force_refresh=args.force_refresh)
    
    if 'error' in data:
        print(f"\n❌ Error: {data['error']}")
    else:
        print(f"\n✅ Success!")
        print(f"\nTitle: {data['title']}")
        print(f"Scraped at: {data['scraped_at']}")
        print(f"\n📊 Statistics:")
        print(f"  - Number of headings: {len(data['headings'])}")
        print(f"  - Number of links: {len(data['links'])}")
        print(f"  - Number of tables: {len(data['tables'])}")
        print(f"  - Total text length: {len(data['full_text'])} characters")
        print(f"\nFirst 500 characters of content:\n{data['full_text'][:500]}")
        
        print("\n" + "="*60)
        print("FORMATTED FOR CHATBOT PROMPT")
        print("="*60)
        print(get_community_context())