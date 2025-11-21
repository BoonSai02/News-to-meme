import requests
from bs4 import BeautifulSoup
import time
import random
import sys
from typing import List, Dict
from src.entity.artifacts import NewsExtractorArtifact
from src.entity.config_entity import NewsExtractorConfig, ConfigEntity
from src.logger import logging
from src.exceptions import CustomException
from src.utils.scraping_utils import make_request_with_retry, extract_links_from_selectors, normalize_url, extract_content_from_listing
from src.utils.text_utils import clean_and_decide_content

class NewsExtractor:
    def __init__(self):
        self.config = NewsExtractorConfig(config=ConfigEntity())
        logging.info("NewsExtractor initialized")

    def extract_from_single_source(self, source_name: str, source_config: Dict) -> List[Dict]:
        """Extract news from a single source"""
        try:
            logging.info(f"Scraping {source_name} for {source_config.get('category', 'general')} news...")
            
            response = make_request_with_retry(
                source_config['url'], 
                self.config.default_headers, 
                self.config.request_timeout,
                self.config.max_retries
            )
            
            if not response:
                logging.warning(f"Failed to get response from {source_name}")
                return []
                
            soup = BeautifulSoup(response.content, 'html.parser')
            links = extract_links_from_selectors(soup, source_config['selectors'])
            
            articles = []
            for i, link in enumerate(links[:self.config.max_articles_per_source]):
                title = link.get_text(strip=True)
                href = link.get('href', '')
                
                if not title or len(title) < self.config.min_title_length:
                    continue
                
                # Normalize URL
                full_url = normalize_url(href, source_config['url'], source_config)
                if not full_url:
                    continue
                
                # Extract content from listing
                listing_content = extract_content_from_listing(link, self.config.max_content_parts)
                final_content = clean_and_decide_content(title, listing_content)
                
                if len(final_content) < self.config.min_content_length:
                    continue
                
                articles.append({
                    'title': title,
                    'content': final_content,
                    'url': full_url,
                    'source': source_name,
                    'category': source_config.get('category', 'entertainment'),
                    'source_index': i
                })
            
            logging.info(f"{source_name}: {len(articles)} articles extracted")
            return articles
            
        except Exception as e:
            logging.error(f"Error extracting from {source_name}: {str(e)}")
            raise CustomException(e, sys)

    def extract_all_sources(self) -> NewsExtractorArtifact:
        """Extract news from all configured sources"""
        try:
            all_articles = []
            sources_scraped = []
            
            for source_name, source_config in self.config.news_sources.items():
                try:
                    articles = self.extract_from_single_source(source_name, source_config)
                    all_articles.extend(articles)
                    sources_scraped.append(source_name)
                    
                    # Apply scraping delay
                    time.sleep(random.uniform(self.config.scraping_delay_min, self.config.scraping_delay_max))
                    
                except Exception as e:
                    logging.error(f"Failed to scrape {source_name}: {str(e)}")
                    continue
            
            logging.info(f"Total articles extracted: {len(all_articles)} from {len(sources_scraped)} sources")
            
            return NewsExtractorArtifact(
                scraped_articles=all_articles,
                total_articles=len(all_articles),
                sources_scraped=sources_scraped
            )
            
        except Exception as e:
            logging.error(f"Error in extract_all_sources: {str(e)}")
            raise CustomException(e, sys)
