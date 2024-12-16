import requests
from bs4 import BeautifulSoup
import yaml
import json
from datetime import datetime
import urllib3
import os
from urllib.parse import urlparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def load_config(config_file='config.yaml'):
    """
    Load website configurations from YAML file
    """
    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_filename_from_url(url):
    """
    Create a safe filename from URL
    """
    parsed = urlparse(url)
    # Get domain name and remove special characters
    domain = parsed.netloc.replace('.', '_').replace('/', '_')
    return f"scraped_{domain}.json"

def save_to_json(data, url):
    """
    Save scraped data to JSON file with filename based on URL
    """
    filename = get_filename_from_url(url)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filename

def scrape_website(config):
    """
    Generic scraping function that takes a configuration dictionary
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    results = []
    try:
        response = requests.get(config['url'], headers=headers, verify=False)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        elements = soup.select(config['selector'])
        
        for element in elements:
            text = element.text.strip()
            results.append({
                "text": text,
                "url": config['url'],
                "timestamp": datetime.now().isoformat()
            })
            print(text)
            
        print(f"Found {len(elements)} elements")
        return results
        
    except Exception as e:
        print(f"Error scraping {config['url']}: {e}")
        return results

if __name__ == "__main__":
    # Load configurations from YAML file
    config = load_config()
    websites = config['websites']
    
    for website in websites:
        print(f"\nScraping {website['url']}...")
        results = scrape_website(website)
        
        if results:  # Only save if we have results
            filename = save_to_json(results, website['url'])
            print(f"Saved {len(results)} items to {filename}")
