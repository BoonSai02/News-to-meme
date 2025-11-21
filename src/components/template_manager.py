from supabase import Client
import random
import sys
from typing import Dict, List, Optional
from src.entity.artifacts import TemplateManagerArtifact
from src.entity.config_entity import TemplateManagerConfig, ConfigEntity
from src.logger import logging
from src.exceptions import CustomException
from src.utils.supabase_utils import load_emotions_from_database, get_template_by_emotion_id, get_random_template, test_schema_access
from src.utils.text_utils import find_most_similar_text


class TemplateManager:
    def __init__(self, supabase_client: Client):
        self.config = TemplateManagerConfig(config=ConfigEntity())
        self.supabase_client = supabase_client
        
        logging.info("Initializing TemplateManager")
        
        # Test schema access first
        test_schema_access(supabase_client, self.config.supabase_schema)
        
        # Load emotions from database (using your working approach)
        logging.info(f"Loading emotions from {self.config.supabase_schema}.{self.config.emotions_table}")
        self.emotions_db = load_emotions_from_database(
            supabase_client, 
            self.config.supabase_schema, 
            self.config.emotions_table
        )
        
        if self.emotions_db:
            logging.info(f"TemplateManager initialized with {len(self.emotions_db)} emotions")
            logging.info(f"Available emotions: {list(self.emotions_db.keys())}")
        else:
            logging.error("TemplateManager initialization failed - no emotions loaded")

    def get_template_from_supabase_smart(self, detected_emotion: str) -> str:
        """Get meme template using the same logic as your working code"""
        try:
            detected_emotion_lower = detected_emotion.lower().strip()
            
            # First, get exact emotion_id match (same as your working code)
            if detected_emotion_lower in self.emotions_db:
                emotion_id = self.emotions_db[detected_emotion_lower]['emotion_id']
                
                template_base64 = get_template_by_emotion_id(
                    self.supabase_client,
                    self.config.supabase_schema,
                    self.config.memes_table,
                    emotion_id
                )
                
                if template_base64:
                    logging.info(f"Found exact match template for {detected_emotion_lower}")
                    return template_base64
            
            # If exact match fails, find nearest emotion (same as your working code)
            available_emotions = list(self.emotions_db.keys())
            nearest_emotion = find_most_similar_text(detected_emotion_lower, available_emotions, self.config.similarity_threshold)
            
            if nearest_emotion and nearest_emotion != detected_emotion_lower:
                emotion_id = self.emotions_db[nearest_emotion]['emotion_id']
                
                template_base64 = get_template_by_emotion_id(
                    self.supabase_client,
                    self.config.supabase_schema,
                    self.config.memes_table,
                    emotion_id
                )
                
                if template_base64:
                    logging.info(f"Found similar match template: {detected_emotion_lower} -> {nearest_emotion}")
                    return template_base64
            
            # If still no match, get any available template (same as your working code)
            template_base64 = get_random_template(
                self.supabase_client,
                self.config.supabase_schema,
                self.config.memes_table
            )
            
            if template_base64:
                logging.info(f"Using random template for {detected_emotion_lower}")
                return template_base64
            else:
                logging.warning("No templates found at all")
                return ""
                
        except Exception as e:
            logging.error(f"Error in template search for {detected_emotion}: {str(e)}")
            return ""

    def match_templates_for_articles(self, processed_articles: List[Dict]) -> TemplateManagerArtifact:
        """Match templates for all processed articles"""
        try:
            matched_templates = []
            unmatched_emotions = []
            emotions_matched = []
            
            logging.info(f"Starting template matching for {len(processed_articles)} articles")
            
            for i, article in enumerate(processed_articles, 1):
                detected_emotion = article.get('emotion', '').strip()
                
                if detected_emotion:
                    # Use the same method as your working code
                    template_base64 = self.get_template_from_supabase_smart(detected_emotion)
                    
                    if template_base64:
                        matched_templates.append(template_base64)
                        emotions_matched.append(detected_emotion)
                        # Set the template base64 in the article for meme generation
                        article['template_base64'] = template_base64
                        article['template_image_path'] = template_base64  # Keep backward compatibility
                        logging.info(f"Article {i}: Template matched for emotion '{detected_emotion}'")
                    else:
                        unmatched_emotions.append(detected_emotion)
                        article['template_base64'] = None
                        article['template_image_path'] = None
                        logging.warning(f"Article {i}: No template found for emotion '{detected_emotion}'")
                else:
                    unmatched_emotions.append("no_emotion_detected")
                    article['template_base64'] = None
                    article['template_image_path'] = None
                    logging.warning(f"Article {i}: No emotion detected")
            
            template_success_rate = (len(matched_templates) / len(processed_articles)) * 100 if processed_articles else 0
            
            logging.info(f"Template matching completed: {len(matched_templates)}/{len(processed_articles)} templates matched ({template_success_rate:.1f}%)")
            
            return TemplateManagerArtifact(
                matched_templates=matched_templates,
                template_success_rate=template_success_rate,
                emotions_matched=emotions_matched,
                unmatched_emotions=unmatched_emotions
            )
            
        except Exception as e:
            logging.error(f"Error in match_templates_for_articles: {str(e)}")
            raise CustomException(e, sys)

    def get_available_emotions(self) -> List[str]:
        """Get list of available emotions from database"""
        if self.emotions_db:
            return list(self.emotions_db.keys())
        else:
            # Return default emotions if database not available
            return ['happy', 'sad', 'angry', 'surprised', 'disgusted', 'fearful', 'sarcasm', 'confused', 'excited', 'bored']














# from supabase import Client
# import random
# import sys
# from typing import Dict, List, Optional
# from src.entity.artifacts import TemplateManagerArtifact
# from src.entity.config_entity import TemplateManagerConfig, ConfigEntity
# from src.logger import logging
# from src.exceptions import CustomException
# from src.utils.supabase_utils import load_emotions_from_database, get_template_by_emotion_id, get_random_template
# from src.utils.text_utils import find_most_similar_text

# class TemplateManager:
#     def __init__(self, supabase_client: Client):
#         self.config = TemplateManagerConfig(config=ConfigEntity())
#         self.supabase_client = supabase_client
        
#         # Load emotions from database - use schema.table format
#         emotions_table = f"{self.config.supabase_schema}.{self.config.emotions_table}"
#         self.emotions_db = load_emotions_from_database(
#             supabase_client, 
#             self.config.supabase_schema, 
#             emotions_table
#         )
        
#         logging.info(f"TemplateManager initialized with {len(self.emotions_db)} emotions")

#     def find_template_by_emotion(self, detected_emotion: str) -> Optional[str]:
#         """Find meme template by emotion with smart matching"""
#         try:
#             detected_emotion_lower = detected_emotion.lower().strip()
            
#             # Use schema.table format for memes table
#             memes_table = f"{self.config.supabase_schema}.{self.config.memes_table}"
            
#             # First, try exact match
#             if detected_emotion_lower in self.emotions_db:
#                 emotion_id = self.emotions_db[detected_emotion_lower]['emotion_id']
#                 template_path = get_template_by_emotion_id(
#                     self.supabase_client,
#                     self.config.supabase_schema,
#                     memes_table,
#                     emotion_id
#                 )
#                 if template_path:
#                     logging.info(f"Found exact emotion match: {detected_emotion_lower}")
#                     return template_path
            
#             # If exact match fails, find nearest emotion
#             available_emotions = list(self.emotions_db.keys())
#             nearest_emotion = find_most_similar_text(
#                 detected_emotion_lower, 
#                 available_emotions, 
#                 self.config.similarity_threshold
#             )
            
#             if nearest_emotion and nearest_emotion != detected_emotion_lower:
#                 emotion_id = self.emotions_db[nearest_emotion]['emotion_id']
#                 template_path = get_template_by_emotion_id(
#                     self.supabase_client,
#                     self.config.supabase_schema,
#                     memes_table,
#                     emotion_id
#                 )
#                 if template_path:
#                     logging.info(f"Found similar emotion match: {detected_emotion_lower} -> {nearest_emotion}")
#                     return template_path
            
#             # If still no match, get random template
#             template_path = get_random_template(
#                 self.supabase_client,
#                 self.config.supabase_schema,
#                 memes_table
#             )
#             if template_path:
#                 logging.info(f"Used random template for emotion: {detected_emotion_lower}")
#                 return template_path
            
#             return None
            
#         except Exception as e:
#             logging.error(f"Error finding template for emotion '{detected_emotion}': {str(e)}")
#             return None

#     def match_templates_for_articles(self, processed_articles: List[Dict]) -> TemplateManagerArtifact:
#         """Match templates for all processed articles"""
#         try:
#             matched_templates = []
#             unmatched_emotions = []
#             emotions_matched = []
            
#             for i, article in enumerate(processed_articles):
#                 detected_emotion = article.get('emotion', '')
                
#                 if detected_emotion:
#                     template_path = self.find_template_by_emotion(detected_emotion)
                    
#                     if template_path:
#                         matched_templates.append(template_path)
#                         emotions_matched.append(detected_emotion)
#                         # Add template path to article
#                         article['template_image_path'] = template_path
#                         logging.info(f"Template matched for article {i+1}: {detected_emotion}")
#                     else:
#                         unmatched_emotions.append(detected_emotion)
#                         article['template_image_path'] = None
#                         logging.warning(f"No template found for article {i+1}: {detected_emotion}")
#                 else:
#                     unmatched_emotions.append("no_emotion")
#                     article['template_image_path'] = None
#                     logging.warning(f"No emotion detected for article {i+1}")
            
#             template_success_rate = (len(matched_templates) / len(processed_articles)) * 100 if processed_articles else 0
            
#             logging.info(f"Template matching completed: {len(matched_templates)}/{len(processed_articles)} templates matched ({template_success_rate:.1f}%)")
            
#             return TemplateManagerArtifact(
#                 matched_templates=matched_templates,
#                 template_success_rate=template_success_rate,
#                 emotions_matched=emotions_matched,
#                 unmatched_emotions=unmatched_emotions
#             )
            
#         except Exception as e:
#             logging.error(f"Error in match_templates_for_articles: {str(e)}")
#             raise CustomException(e, sys)

#     def get_available_emotions(self) -> List[str]:
#         """Get list of available emotions from database"""
#         return list(self.emotions_db.keys())


