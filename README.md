# News Web Scraper

Automated web scraper that collects news from various Polish government and military websites and converts them to RSS feeds.

## Features

- Scrapes multiple news websites
- Generates RSS feeds
- Automated running every 6 hours via GitHub Actions
- Comprehensive logging system
- Artifact storage for logs and feeds

## Configuration

The scraping targets are configured in `config.yaml`. Each website entry requires:
- `url`: The website URL to scrape
- `selector` or `selectors`: CSS selector(s) to find news items

## Setup

1. Clone the repository
2. Install dependencies:
