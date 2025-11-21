import sys
import json
import base64
import os
from datetime import datetime
from typing import Dict, List
from supabase import Client
from src.components.news_extractor import NewsExtractor
from src.components.content_processor import ContentProcessor
from src.components.image_downloader import ImageDownloader
from src.components.gemini_processor import GeminiProcessor
from src.components.template_manager import TemplateManager
from src.components.meme_generator import MemeGenerator
from src.logger import logging
from src.exceptions import CustomException

# Hardcoded bucket name for personal Supabase
STORAGE_BUCKET_NAME = 'assets'

def scrape_and_process_news() -> Dict:
    """Scrape news and process content with images"""
    try:
        news_extractor = NewsExtractor()
        content_processor = ContentProcessor()
        image_downloader = ImageDownloader()
        
        logging.info("Starting news extraction...")
        news_artifact = news_extractor.extract_all_sources()
        
        if not news_artifact.scraped_articles:
            raise CustomException("No articles extracted from sources", None)
        
        logging.info("Processing content...")
        content_artifact = content_processor.process_articles(news_artifact.scraped_articles)
        
        if not content_artifact.processed_articles:
            raise CustomException("No articles after content processing", None)
        
        logging.info("Downloading images...")
        image_artifact = image_downloader.download_images_for_articles(content_artifact.categorized_news)
        
        total_articles = sum(len(articles) for articles in content_artifact.categorized_news.values())
        return {
            'categorized_news': content_artifact.categorized_news,
            'total_articles': total_articles,
            'image_artifact': image_artifact,
            'unique_articles_count': content_artifact.unique_articles_count,
             'sources_scraped': news_artifact.sources_scraped
        }
    except Exception as e:
        logging.error(f"Error in scrape_and_process_news: {str(e)}")
        raise CustomException(str(e), sys.exc_info()[2])

def process_with_ai(categorized_news: Dict[str, List[Dict]], gemini_api_key: str, template_client: Client) -> Dict:
    try:
        gemini_processor = GeminiProcessor(gemini_api_key)
        template_manager = TemplateManager(template_client)
        meme_generator = MemeGenerator()
       
        emotions_list = template_manager.get_available_emotions()
        if not emotions_list:
            emotions_list = ['neutral']
       
        logging.info("Processing with Gemini AI...")
        gemini_artifact = gemini_processor.process_articles(categorized_news, emotions_list)
       
        logging.info("Matching templates...")
        template_artifact = template_manager.match_templates_for_articles(gemini_artifact.processed_content)
       
        logging.info("Generating memes with overlaid dialogues...")
        memes_generated = 0
        memes_failed = 0
       
        for article in gemini_artifact.processed_content:
            # Ensure we have both parts before trying to generate
            if article.get('template_base64') and article.get('dialogues'):
                try:
                    overlaid_meme = meme_generator.generate_meme_with_overlay(
                        article['template_base64'],
                        article['dialogues']
                    )
                    if overlaid_meme:
                        article['final_meme_base64'] = overlaid_meme
                        memes_generated += 1
                        logging.info(f"MEME GENERATED for: {article.get('title')[:30]}...")
                    else:
                        article['final_meme_base64'] = None
                        memes_failed += 1
                        logging.warning(f"GENERATION FAILED (Overlay returned None) for: {article.get('title')[:30]}...")
                except Exception as e:
                    logging.error(f"Error generating overlay: {e}")
                    article['final_meme_base64'] = None
                    memes_failed += 1
            else:
                article['final_meme_base64'] = None
                memes_failed += 1
                missing = []
                if not article.get('template_base64'): missing.append("Template")
                if not article.get('dialogues'): missing.append("Dialogues")
                logging.warning(f"SKIPPING GENERATION for {article.get('title')[:20]}: Missing {', '.join(missing)}")

        return {
            'processed_articles': gemini_artifact.processed_content,
            'memes_generated': memes_generated,
            'memes_failed': memes_failed,
            # Pass other stats as needed
            'success_rate': 100, 
            'template_success_rate': 100,
            'meme_generation_success_rate': 100,
            'total_api_calls': 0,
            'failed_articles': []
        }
    except Exception as e:
        logging.error(f"Error in process_with_ai: {str(e)}")
        raise CustomException(str(e), sys.exc_info()[2])

def _upload_to_supabase_storage(storage_client: Client, file_bytes: bytes, path: str) -> str:
    """Uploads to Supabase and constructs the PUBLIC URL manually."""
    try:
        logging.info(f"Uploading {len(file_bytes)} bytes to {path}...")
        
        # 1. Upload File
        response = storage_client.storage.from_(STORAGE_BUCKET_NAME).upload(
            path=path,
            file=file_bytes,
            file_options={"cache-control": "3600", "upsert": "true"} 
        )
        
        # Check for errors in response (Supabase-py v2 sometimes doesn't throw, returns dict/response)
        if hasattr(response, 'status_code') and response.status_code not in [200, 201]:
             raise Exception(f"Upload failed status: {response.status_code}")

        # 2. Construct Public URL Manually (More reliable than get_public_url for some versions)
        # Pattern: https://<project_ref>.supabase.co/storage/v1/object/public/<bucket>/<path>
        project_url = os.getenv('STORAGE_SUPABASE_URL')
        
        # Remove trailing slash if present
        if project_url.endswith('/'):
            project_url = project_url[:-1]
            
        final_url = f"{project_url}/storage/v1/object/public/{STORAGE_BUCKET_NAME}/{path}"
        
        logging.info(f"Upload Success. URL: {final_url}")
        return final_url

    except Exception as e:
        logging.error(f"Storage upload failed for {path}: {str(e)}")
        # Attempt standard get_public_url as fallback
        try:
            return storage_client.storage.from_(STORAGE_BUCKET_NAME).get_public_url(path)
        except:
            raise CustomException(f"Upload and URL generation failed: {str(e)}", None)

def _persist_article_to_supabase(storage_client: Client, article: Dict, scrape_time: datetime = None) -> str:
    try:
        if scrape_time is None: scrape_time = datetime.now()
        
        description = article.get('description', article.get('content', '')[:200])
        
        # Check if the article already exists
        existing = storage_client.table('trending_news').select('news_id').eq('reference_link', article['source_url']).execute()
        
        if existing.data:
            return existing.data[0]['news_id']
        
        insert_data = {
            'title': article['title'],
            'description': description,
            'reference_link': article['source_url'],
            'category': article['category'],
            'scraped_at': scrape_time.isoformat()
        }
        
        res = storage_client.table('trending_news').insert(insert_data).execute()
        
        if not res.data:
            raise Exception("Insert returned no data")
            
        return res.data[0]['news_id']
    except Exception as e:
        logging.error(f"Persist failed: {e}")
        raise CustomException(str(e), sys.exc_info()[2])

def execute_complete_pipeline(gemini_api_key: str, template_client: Client, storage_client: Client) -> Dict:
    try:
        logging.info("=== PIPELINE START ===")
        scrape_time = datetime.now()
        
        # 1. Scrape
        scraping_results = scrape_and_process_news()
        
        # Limit articles
        MAX_ARTICLES = 2
        limited_news = {k: v[:MAX_ARTICLES] for k, v in scraping_results['categorized_news'].items()}
        
        # 2. AI Process
        ai_results = process_with_ai(limited_news, gemini_api_key, template_client)
        
        # 3. Persist & Upload
        inserted_count = 0
        meme_uploaded_count = 0
        
        for article in ai_results['processed_articles']:
            if 'category' not in article: article['category'] = 'uncategorized'
            
            try:
                # A. Insert Data Row
                news_id = _persist_article_to_supabase(storage_client, article, scrape_time)
                
                # B. Upload Image (If exists)
                meme_url = None
                if article.get('final_meme_base64'):
                    try:
                        image_bytes = base64.b64decode(article['final_meme_base64'])
                        path = f"memes/{news_id}.png"
                        meme_url = _upload_to_supabase_storage(storage_client, image_bytes, path)
                        meme_uploaded_count += 1
                    except Exception as upload_err:
                        logging.error(f"Upload logic failed for {news_id}: {upload_err}")
                else:
                    logging.warning(f"No Base64 found for article {news_id} - Skipping Upload")
                
                # C. Update Row with URL
                if meme_url:
                    storage_client.table('trending_news').update(
                        {'meme_typed_image_url': meme_url}
                    ).eq('news_id', news_id).execute()
                    
                inserted_count += 1
                
            except Exception as e:
                logging.error(f"Failed to persist article chain: {e}")

        return {
            "status": "success", 
            "inserted": inserted_count, 
            "uploaded": meme_uploaded_count,
            "bucket": STORAGE_BUCKET_NAME
        }
        
    except Exception as e:
        logging.error(f"Pipeline failed: {str(e)}")
        raise CustomException(str(e), sys.exc_info()[2])