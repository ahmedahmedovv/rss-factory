import requests
from bs4 import BeautifulSoup
import yaml
import urllib3
from datetime import datetime
from urllib.parse import urlparse
import re
from feedgen.feed import FeedGenerator
import pytz
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def clean_text(text):
    """
    Clean the text by removing extra whitespace, newlines and HTML tags
    """
    text = re.sub(r'<[^>]+>', '', text)
    text = ' '.join(text.split())
    return text.strip()

def load_config(config_file='config.yaml'):
    """
    Load website configurations from YAML file
    """
    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_filename_from_url(url):
    """
    Create a safe filename from URL while preserving the exact path
    """
    parsed = urlparse(url)
    # Get domain and path, replace unsafe characters
    domain = parsed.netloc
    path = parsed.path.strip('/')
    
    # Create safe filename by replacing unsafe characters
    safe_name = f"{domain}_{path}".replace('/', '_').replace('.', '_')
    
    # Ensure the filename isn't too long
    if len(safe_name) > 200:  # reasonable max length for filename
        safe_name = safe_name[:200]
    
    return f"feed_{safe_name}.xml"

def create_rss_feed(data, url):
    """
    Create RSS feed from scraped data and save it in the data folder
    """
    # Create data directory if it doesn't exist
    data_dir = 'data'
    os.makedirs(data_dir, exist_ok=True)
    
    fg = FeedGenerator()
    fg.title(f'Scraped News from {urlparse(url).netloc}')
    fg.description('Automatically generated feed from scraped content')
    fg.link(href=url)
    fg.language('pl')
    
    # Set timezone to Poland
    poland_tz = pytz.timezone('Europe/Warsaw')
    
    for item in data:
        fe = fg.add_entry()
        fe.title(item['text'])
        fe.link(href=item['url'])
        fe.description(item['text'])
        # Convert timestamp to datetime with timezone
        timestamp = datetime.fromisoformat(item['timestamp'])
        local_timestamp = poland_tz.localize(timestamp)
        fe.published(local_timestamp)
        
    filename = get_filename_from_url(url)
    # Save file in the data directory
    full_path = os.path.join(data_dir, filename)
    fg.rss_file(full_path)
    return full_path

def scrape_website(config):
    """
    Generic scraping function that handles multiple selectors
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    results = []
    try:
        response = requests.get(config['url'], headers=headers, verify=False)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Handle either single selector (string) or multiple selectors (list)
        selectors = config.get('selectors', [config.get('selector')])
        
        for selector in selectors:
            elements = soup.select(selector)
            
            for element in elements:
                text = clean_text(element.text)
                if text:
                    results.append({
                        "text": text,
                        "url": config['url'],
                        "timestamp": datetime.now().isoformat()
                    })
                    print(f"Found from selector {selector}: {text}")
            
            print(f"Found {len(elements)} elements with selector: {selector}")
            
        return results
        
    except Exception as e:
        print(f"Error scraping {config['url']}: {e}")
        return results

if __name__ == "__main__":
    # First, install required package:
    # pip install feedgen pytz
    
    config = load_config()
    websites = config['websites']
    
    for website in websites:
        print(f"\nScraping {website['url']}...")
        results = scrape_website(website)
        
        if results:
            filename = create_rss_feed(results, website['url'])
            print(f"Created RSS feed with {len(results)} items in {filename}")
