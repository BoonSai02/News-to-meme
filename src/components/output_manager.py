import json
import os
from pathlib import Path
from datetime import datetime
import sys
from typing import Dict, List
from src.entity.artifacts import OutputManagerArtifact
from src.entity.config_entity import OutputManagerConfig, ConfigEntity
from src.logger import logging
from src.exceptions import CustomException


class OutputManager:
    def __init__(self):
        self.config = OutputManagerConfig(config=ConfigEntity())
        self.setup_output_directory()
        logging.info("OutputManager initialized")

    def setup_output_directory(self):
        """Setup output directory structure"""
        try:
            output_path = Path(self.config.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            logging.info(f"Output directory ensured: {output_path}")
        except Exception as e:
            logging.error(f"Error creating output directory: {str(e)}")
            raise CustomException(e, sys)

    def save_clean_categorized_news(self, categorized_news: Dict[str, List[Dict]]) -> str:
        """Save categorized news with only required fields"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
            filename = f"{self.config.news_data_prefix}_{timestamp}{self.config.json_extension}"
            file_path = Path(self.config.output_dir) / filename
            
            # Clean the data to keep only required fields
            clean_categorized_news = {}
            for category, articles in categorized_news.items():
                clean_articles = []
                for article in articles:
                    clean_article = {
                        "content": article.get('content', ''),
                        "image_path": article.get('image_path'),
                        "url": article.get('url', '')
                    }
                    clean_articles.append(clean_article)
                clean_categorized_news[category] = clean_articles
            
            total_articles = sum(len(articles) for articles in clean_categorized_news.values())
            total_images = sum(1 for articles in clean_categorized_news.values() 
                             for article in articles if article.get('image_path'))
            
            json_data = {
                'timestamp': datetime.now().isoformat(),
                'total_articles': total_articles,
                'total_images': total_images,
                'categories': list(clean_categorized_news.keys()),
                'categorized_news': clean_categorized_news
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            file_size = os.path.getsize(file_path)
            
            logging.info(f"Clean categorized news saved to: {filename}")
            logging.info(f"Total articles: {total_articles}, Images: {total_images}, File size: {file_size} bytes")
            
            return str(file_path)
            
        except Exception as e:
            logging.error(f"Error saving categorized news: {str(e)}")
            raise CustomException(e, sys)

    def save_clean_processed_memes(self, processed_articles: List[Dict]) -> OutputManagerArtifact:
        """Save processed meme data with base64 templates and final memes"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
            filename = f"{self.config.processed_memes_prefix}_{timestamp}{self.config.json_extension}"
            file_path = Path(self.config.output_dir) / filename
            
            # Clean the data to keep only required fields
            clean_articles = []
            for article in processed_articles:
                clean_article = {
                    "category": article.get('category', ''),
                    "description": article.get('description', ''),
                    "template_base64": article.get('template_base64'),  # Raw template from Supabase
                    "final_meme_base64": article.get('final_meme_base64'),  # Template with overlaid text
                    "image_path": article.get('image_path'),
                    "dialogues": article.get('dialogues', []),
                    "hashtags": article.get('hashtags', []),
                    "url": article.get('url', ''),
                    "emotion": article.get('emotion', ''),
                    "template_matched": bool(article.get('template_base64'))
                }
                clean_articles.append(clean_article)
            
            # Calculate statistics
            templates_found = len([a for a in clean_articles if a.get('template_base64')])
            final_memes_generated = len([a for a in clean_articles if a.get('final_meme_base64')])
            images_found = len([a for a in clean_articles if a.get('image_path')])
            
            output_data = {
                'timestamp': datetime.now().isoformat(),
                'total_processed': len(clean_articles),
                'templates_matched': templates_found,
                'final_memes_generated': final_memes_generated,
                'images_found': images_found,
                'meme_generation_success_rate': (final_memes_generated / templates_found * 100) if templates_found > 0 else 0.0,
                'processed_memes': clean_articles
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            file_size = os.path.getsize(file_path)
            
            logging.info(f"Clean processed memes saved to: {filename}")
            logging.info(f"Articles: {len(clean_articles)}, Templates: {templates_found}, Final Memes: {final_memes_generated}")
            
            return OutputManagerArtifact(
                output_file_path=str(file_path),
                total_articles_saved=len(clean_articles),
                file_size_bytes=file_size,
                timestamp=timestamp
            )
            
        except Exception as e:
            logging.error(f"Error saving processed memes: {str(e)}")
            raise CustomException(e, sys)










# import json
# import os
# from pathlib import Path
# from datetime import datetime
# import sys
# from typing import Dict, List
# from src.entity.artifacts import OutputManagerArtifact
# from src.entity.config_entity import OutputManagerConfig, ConfigEntity
# from src.logger import logging
# from src.exceptions import CustomException

# class OutputManager:
#     def __init__(self):
#         self.config = OutputManagerConfig(config=ConfigEntity())
#         self.setup_output_directory()
#         logging.info("OutputManager initialized")

#     def setup_output_directory(self):
#         """Setup output directory structure"""
#         try:
#             output_path = Path(self.config.output_dir)
#             output_path.mkdir(parents=True, exist_ok=True)
#             logging.info(f"Output directory ensured: {output_path}")
#         except Exception as e:
#             logging.error(f"Error creating output directory: {str(e)}")
#             raise CustomException(e, sys)

#     def save_clean_categorized_news(self, categorized_news: Dict[str, List[Dict]]) -> str:
#         """Save categorized news with only required fields"""
#         try:
#             timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
#             filename = f"{self.config.news_data_prefix}_{timestamp}{self.config.json_extension}"
#             file_path = Path(self.config.output_dir) / filename
            
#             # Clean the data to keep only required fields
#             clean_categorized_news = {}
#             for category, articles in categorized_news.items():
#                 clean_articles = []
#                 for article in articles:
#                     clean_article = {
#                         "content": article.get('content', ''),
#                         "image_path": article.get('image_path'),
#                         "url": article.get('url', '')
#                     }
#                     clean_articles.append(clean_article)
#                 clean_categorized_news[category] = clean_articles
            
#             total_articles = sum(len(articles) for articles in clean_categorized_news.values())
#             total_images = sum(1 for articles in clean_categorized_news.values() 
#                              for article in articles if article.get('image_path'))
            
#             json_data = {
#                 'timestamp': datetime.now().isoformat(),
#                 'total_articles': total_articles,
#                 'total_images': total_images,
#                 'categories': list(clean_categorized_news.keys()),
#                 'categorized_news': clean_categorized_news
#             }
            
#             with open(file_path, 'w', encoding='utf-8') as f:
#                 json.dump(json_data, f, indent=2, ensure_ascii=False)
            
#             file_size = os.path.getsize(file_path)
            
#             logging.info(f"Clean categorized news saved to: {filename}")
#             logging.info(f"Total articles: {total_articles}, Images: {total_images}, File size: {file_size} bytes")
            
#             return str(file_path)
            
#         except Exception as e:
#             logging.error(f"Error saving categorized news: {str(e)}")
#             raise CustomException(e, sys)

#     def save_clean_processed_memes(self, processed_articles: List[Dict]) -> OutputManagerArtifact:
#         """Save processed meme data with only required fields"""
#         try:
#             timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
#             filename = f"{self.config.processed_memes_prefix}_{timestamp}{self.config.json_extension}"
#             file_path = Path(self.config.output_dir) / filename
            
#             # Clean the data to keep only required fields
#             clean_articles = []
#             for article in processed_articles:
#                 clean_article = {
#                     "category": article.get('category', ''),
#                     "description": article.get('description', ''),
#                     "template_path": article.get('template_image_path'),  # Note: template_image_path -> template_path
#                     "image_path": article.get('image_path'),
#                     "dialogues": article.get('dialogues', []),
#                     "hashtags": article.get('hashtags', []),
#                     "url": article.get('url', '')
#                 }
#                 clean_articles.append(clean_article)
            
#             # Calculate statistics
#             templates_found = len([a for a in clean_articles if a.get('template_path')])
#             images_found = len([a for a in clean_articles if a.get('image_path')])
            
#             output_data = {
#                 'timestamp': datetime.now().isoformat(),
#                 'total_processed': len(clean_articles),
#                 'templates_matched': templates_found,
#                 'images_found': images_found,
#                 'processed_memes': clean_articles
#             }
            
#             with open(file_path, 'w', encoding='utf-8') as f:
#                 json.dump(output_data, f, indent=2, ensure_ascii=False)
            
#             file_size = os.path.getsize(file_path)
            
#             logging.info(f"Clean processed memes saved to: {filename}")
#             logging.info(f"Articles: {len(clean_articles)}, Templates: {templates_found}, Images: {images_found}")
            
#             return OutputManagerArtifact(
#                 output_file_path=str(file_path),
#                 total_articles_saved=len(clean_articles),
#                 file_size_bytes=file_size,
#                 timestamp=timestamp
#             )
            
#         except Exception as e:
#             logging.error(f"Error saving processed memes: {str(e)}")
#             raise CustomException(e, sys)

