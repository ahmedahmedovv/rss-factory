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
import logging
import sys
from dotenv import load_dotenv
from supabase import create_client, Client
import io

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv()

def init_supabase() -> Client:
    """Initialize Supabase client using environment variables"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")
    
    return create_client(
        supabase_url=url,
        supabase_key=key
    )

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
    Create RSS feed from scraped data and save it to Supabase storage
    """
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
        timestamp = datetime.fromisoformat(item['timestamp'])
        local_timestamp = poland_tz.localize(timestamp)
        fe.published(local_timestamp)
    
    # Generate filename
    filename = get_filename_from_url(url)
    
    # Initialize Supabase client
    supabase = init_supabase()
    
    # Generate RSS content as bytes
    feed_content = fg.rss_str()
    
    try:
        # Convert feed_content to bytes if it isn't already
        if not isinstance(feed_content, bytes):
            feed_content = feed_content.encode('utf-8')
        
        # Upload to Supabase storage
        response = supabase.storage \
            .from_('rss_storage') \
            .upload(
                path=filename,
                file=feed_content,
                file_options={
                    "content-type": "application/rss+xml",
                    "x-upsert": "true"  # This will update the file if it already exists
                }
            )
        
        # Get public URL
        public_url = supabase.storage \
            .from_('rss_storage') \
            .get_public_url(filename)
            
        return public_url
        
    except Exception as e:
        logging.error(f"Error uploading to Supabase: {str(e)}")
        raise

def setup_logging():
    """
    Configure logging system with both file and console output in a dedicated log folder
    """
    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # Create a unique log filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f'scraping_{timestamp}.log'
    
    # Create full path for log file
    log_filepath = os.path.join(log_dir, log_filename)
    
    # Configure logging format
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Set up root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Create console handler with custom formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    logger.addHandler(console_handler)
    
    # Create file handler
    file_handler = logging.FileHandler(log_filepath)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    logger.addHandler(file_handler)
    
    return logger

def scrape_website(config):
    """
    Generic scraping function that handles multiple selectors with improved error handling
    """
    logger = logging.getLogger()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    
    results = []
    try:
        logger.info(f"Starting to scrape: {config['url']}")
        
        # Add retry mechanism
        session = requests.Session()
        retries = urllib3.util.Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504]
        )
        session.mount('https://', requests.adapters.HTTPAdapter(max_retries=retries))
        
        # Add timeout and additional parameters
        response = session.get(
            config['url'],
            headers=headers,
            verify=False,  # Only if SSL verification is causing issues
            timeout=(10, 30),  # (connect timeout, read timeout)
            allow_redirects=True
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        selectors = config.get('selectors', [config.get('selector')])
        
        for selector in selectors:
            elements = soup.select(selector)
            logger.info(f"Found {len(elements)} elements with selector: {selector}")
            
            for element in elements:
                text = clean_text(element.text)
                if text:
                    results.append({
                        "text": text,
                        "url": config['url'],
                        "timestamp": datetime.now().isoformat()
                    })
                    logger.debug(f"Scraped content: {text[:100]}...")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while scraping {config['url']}: {str(e)}")
        logger.error(f"Response status code: {getattr(e.response, 'status_code', 'N/A')}")
        logger.error(f"Response headers: {getattr(e.response, 'headers', 'N/A')}")
    except Exception as e:
        logger.error(f"Unexpected error while scraping {config['url']}: {str(e)}")
        logger.exception("Full traceback:")
    
    return results

if __name__ == "__main__":
    # Setup logging
    logger = setup_logging()
    logger.info("Starting web scraping process")
    
    try:
        config = load_config()
        websites = config['websites']
        
        for website in websites:
            logger.info(f"Processing website: {website['url']}")
            results = scrape_website(website)
            
            if results:
                public_url = create_rss_feed(results, website['url'])
                logger.info(f"Created RSS feed with {len(results)} items at {public_url}")
            else:
                logger.warning(f"No results found for {website['url']}")
                
    except Exception as e:
        logger.critical(f"Critical error in main process: {str(e)}")
        logger.exception("Full traceback:")
        sys.exit(1)
        
    logger.info("Web scraping process completed")
