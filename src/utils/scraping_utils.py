import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Dict, List, Optional
import sys
from src.logger import logging
from src.exceptions import CustomException
from src.constants import get_random_user_agent

def make_request_with_retry(url: str, headers: Dict, timeout: int, max_retries: int = 3) -> Optional[requests.Response]:
    """Make HTTP request with retry logic"""
    for attempt in range(max_retries):
        try:
            # Update user agent for each request
            headers['User-Agent'] = get_random_user_agent()
            response = requests.get(url, headers=headers, timeout=timeout)
            if response.status_code == 200:
                return response
            else:
                logging.warning(f"Request failed with status {response.status_code} for {url}")
        except Exception as e:
            if attempt == max_retries - 1:
                logging.error(f"All retry attempts failed for {url}: {str(e)}")
                raise CustomException(e, sys)
            logging.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
    return None

def extract_links_from_selectors(soup: BeautifulSoup, selectors: List[str]) -> List:
    """Extract links using multiple CSS selectors"""
    all_links = []
    for selector in selectors:
        links = soup.select(selector)
        all_links.extend(links)
    return all_links

def normalize_url(href: str, base_url: str, source_config: Dict) -> str:
    """Normalize and construct full URLs"""
    if not href or len(href) < 3:
        return ""
    
    if href.startswith('http'):
        return href
    elif href.startswith('/'):
        base_domain = source_config['url'].split('/')[2]
        if 'timesofindia' in base_domain:
            return 'https://timesofindia.indiatimes.com' + href
        elif 'indianexpress' in base_domain:
            return 'https://indianexpress.com' + href
        elif 'hindustantimes' in base_domain:
            return 'https://www.hindustantimes.com' + href
        elif 'news18' in base_domain:
            return 'https://www.news18.com' + href
        elif 'economictimes' in base_domain:
            return 'https://economictimes.indiatimes.com' + href
        elif 'livemint' in base_domain:
            return 'https://www.livemint.com' + href
        elif 'moneycontrol' in base_domain:
            return 'https://www.moneycontrol.com' + href
        else:
            return source_config['url'].split('/')[0] + '//' + base_domain + href
    return ""

def extract_content_from_listing(link_element, max_parts: int = 3) -> str:
    """Extract content from article listing"""
    try:
        container = link_element.parent
        content_parts = []
        
        if container:
            content_elements = container.select('.summary, .snippet, p, .description')[:5]
            for elem in content_elements:
                text = elem.get_text(strip=True)
                if len(text) > 10 and text != link_element.get_text(strip=True):
                    content_parts.append(text)
        
        full_content = ' '.join(content_parts[:max_parts])
        return full_content[:800] if full_content else ""
    except Exception:
        return ""

