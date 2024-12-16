import requests
from bs4 import BeautifulSoup
import json

def scrape_pap_titles():
    # URL of the website
    url = "https://www.pap.pl/kraj?page=0"
    
    # Add headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Create a list to store the articles
    articles = []
    
    try:
        # Send HTTP GET request with headers
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Debug: Print status code and content length
        print(f"Status Code: {response.status_code}")
        print(f"Content Length: {len(response.text)}")
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Debug: Try different selectors
        titles = soup.select('.title')  # Original selector
        if not titles:
            print("\nTrying alternative selectors...")
            titles = soup.select('.title')  # Try just .title
            if not titles:
                titles = soup.find_all('font')  # Try all font elements
        
        # Print each title
        if titles:
            print("\nFound titles:\n")
            for title in titles:
                # Get the title text and link
                title_link = title.find('a')
                if title_link:
                    article_data = {
                        'title': title_link.text.strip(),
                        'url': f"https://www.pap.pl{title_link.get('href', '')}"
                    }
                    articles.append(article_data)
            
            # Save to JSON file
            with open('pap_articles.json', 'w', encoding='utf-8') as f:
                json.dump(articles, f, ensure_ascii=False, indent=2)
            
            print(f"Successfully saved {len(articles)} articles to pap_articles.json")
        else:
            print("No titles found.")
            # Debug: Print some of the HTML to inspect structure
            print("\nPage HTML snippet:")
            print(soup.prettify()[:1000])
            
    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    print("Scraping titles from PAP.pl...")
    scrape_pap_titles()
