import requests
from bs4 import BeautifulSoup
import yaml
import json
from datetime import datetime

def load_config(config_file='config.yaml'):
    """
    Load website configurations from YAML file
    """
    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def scrape_website(config):
    """
    Generic scraping function that takes a configuration dictionary
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    results = []
    try:
        response = requests.get(config['url'], headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Use the selector specified in the config
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

def save_to_json(data, filename='scraped_data.json'):
    """
    Save scraped data to JSON file
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    # Load configurations from YAML file
    config = load_config()
    websites = config['websites']
    
    all_results = []
    
    for website in websites:
        print(f"\nScraping {website['url']}...")
        results = scrape_website(website)
        all_results.extend(results)
    
    # Save all results to JSON file
    save_to_json(all_results)
    print(f"\nSaved {len(all_results)} items to scraped_data.json")
