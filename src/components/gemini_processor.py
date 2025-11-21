import os
import json
import re
import time
import warnings
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
import sys
from typing import List, Dict, Optional
from src.entity.artifacts import GeminiProcessorArtifact
from src.entity.config_entity import GeminiProcessorConfig, ConfigEntity
from src.logger import logging
from src.exceptions import CustomException
from src.constants import GEMINI_COMPREHENSIVE_PROMPT

# Suppress Google Cloud warnings
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GLOG_minloglevel'] = '2'
warnings.filterwarnings("ignore", category=UserWarning, module="google.auth")

class GeminiProcessor:
    def __init__(self, api_key: str):
        self.config = GeminiProcessorConfig(config=ConfigEntity())
        
        if not api_key:
            raise CustomException("No valid Gemini API key provided", sys)
        
        self.api_key = api_key
        
        # Configure Gemini
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.config.gemini_model_name)
        
        logging.info("GeminiProcessor initialized with single API key")

    def create_comprehensive_prompt(self, news_content: str, emotions_list: List[str]) -> str:
        """Create comprehensive prompt using template from constants"""
        emotion_options = '\n'.join([f"- {emotion}" for emotion in emotions_list])
        
        return GEMINI_COMPREHENSIVE_PROMPT.format(
            news_content=news_content,
            emotion_options=emotion_options
        )

    def safe_gemini_call(self, prompt: str) -> str:
        """Make Gemini API call with proper error handling"""
        for attempt in range(self.config.max_gemini_retries):
            try:
                logging.info(f"Making Gemini API call (attempt {attempt + 1})")
                
                # Make the API call
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    response = self.model.generate_content(prompt)
                
                # Apply rate limiting
                time.sleep(self.config.api_call_delay)
                
                return response.text.strip()
            
            except google_exceptions.PermissionDenied as e:
                raise CustomException("Gemini API key is invalid or expired. Please check your .env file.", sys) from e
            
            except google_exceptions.ResourceExhausted as e:
                raise CustomException("Gemini API quota exceeded. Please check your billing or wait.", sys) from e
                
            except Exception as e:
                error_msg = str(e)
                # Clean Google Cloud warnings from error message
                if "ALTS creds ignored" not in error_msg:
                    logging.warning(f"API call attempt {attempt + 1} failed: {error_msg}")
                
                if attempt < self.config.max_gemini_retries - 1:
                    time.sleep(5)
                else:
                    clean_error = error_msg.replace("ALTS creds ignored. Not running on GCP and untrusted ALTS is not enabled.", "").strip()
                    raise CustomException(f"All API attempts failed: {clean_error}", sys)

    def validate_and_fix_dialogues(self, dialogues: List[str]) -> List[str]:
        """Validate and fix dialogue format - ensure single lines with no \n"""
        fixed_dialogues = []
        
        for dialogue in dialogues[:2]:  # Only take first 2 dialogues
            if isinstance(dialogue, str):
                # Remove any \n or actual newlines and clean up
                clean_dialogue = dialogue.replace('\\n', ' ').replace('\n', ' ').strip()
                
                # Split by spaces and limit to 10 words max
                words = clean_dialogue.split()
                if len(words) > 10:
                    words = words[:10]
                
                final_dialogue = ' '.join(words)
                
                if final_dialogue:
                    fixed_dialogues.append(final_dialogue)
                else:
                    # Generate fallback single-line dialogues
                    fallback = [
                        "This news is so predictable everyone already knew",
                        "Not surprised at all honestly expected this"
                    ]
                    fixed_dialogues.append(fallback[len(fixed_dialogues)])
        
        # Ensure we have exactly 2 dialogues
        while len(fixed_dialogues) < 2:
            fallback_dialogues = [
                "News like this be like absolutely nobody surprised",
                "Everyone after reading this news zero shock value"
            ]
            fixed_dialogues.append(fallback_dialogues[len(fixed_dialogues)])
        
        return fixed_dialogues[:2]

    def parse_gemini_response(self, response: str) -> Optional[Dict]:
        """Parse JSON response from Gemini with proper dialogue validation"""
        try:
            # Try to extract JSON from response
            json_pattern = r'\{.*?\}'
            json_match = re.search(json_pattern, response, re.DOTALL)
            
            if json_match:
                json_text = json_match.group(0)
                parsed = json.loads(json_text)
                
                required_fields = ['description', 'emotion', 'category', 'dialogues', 'hashtags']
                if all(key in parsed for key in required_fields):
                    # Validate and fix dialogues
                    if 'dialogues' in parsed and isinstance(parsed['dialogues'], list):
                        parsed['dialogues'] = self.validate_and_fix_dialogues(parsed['dialogues'])
                    
                    logging.info("Successfully parsed Gemini response")
                    return parsed
                    
            return self.manual_parse_response(response)
            
        except json.JSONDecodeError:
            return self.manual_parse_response(response)
        except Exception as e:
            logging.error(f"Error parsing Gemini response: {str(e)}")
            return None

    def manual_parse_response(self, response: str) -> Optional[Dict]:
        """Manually parse response if JSON parsing fails"""
        try:
            result = {}
            
            # Extract description
            desc_patterns = [
                r'"?description"?\s*:\s*"([^"]+)"',
                r'description[:\s]+(.+?)(?=emotion|category|\n\n)',
            ]
            
            for pattern in desc_patterns:
                desc_match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
                if desc_match:
                    result['description'] = desc_match.group(1).strip()
                    break
            
            if 'description' not in result:
                result['description'] = "Another predictable news story that surprises nobody"
            
            # Extract emotion
            emotion_match = re.search(r'"?emotion"?\s*:\s*"?(\w+)"?', response, re.IGNORECASE)
            result['emotion'] = emotion_match.group(1).lower() if emotion_match else 'sarcasm'
            
            # Extract category
            category_match = re.search(r'"?category"?\s*:\s*"?(\w+)"?', response, re.IGNORECASE)
            result['category'] = category_match.group(1) if category_match else 'entertainment'
            
            # Generate fallback dialogues - single lines only
            fallback_dialogues = [
                "When news tries to surprise us but everyone already knew",
                "Me after reading this news absolutely zero shock here"
            ]
            
            # Try to extract dialogues from response
            dialogue_quotes = re.findall(r'"([^"]+)"', response)
            good_dialogues = []
            
            for quote in dialogue_quotes:
                # Clean any \n or newlines and limit words
                clean_quote = quote.replace('\\n', ' ').replace('\n', ' ').strip()
                words = clean_quote.split()
                if 4 <= len(words) <= 10:  # Good length for single-line dialogue
                    good_dialogues.append(' '.join(words))
            
            if len(good_dialogues) >= 2:
                result['dialogues'] = good_dialogues[:2]
            else:
                result['dialogues'] = fallback_dialogues
            
            # Extract hashtags
            hashtags = re.findall(r'#\w+', response)
            if len(hashtags) >= 4:
                result['hashtags'] = hashtags[:8]
            else:
                result['hashtags'] = ["#SavageNews", "#MemeWorthy", "#ViralContent", "#Sarcasm", "#Buzzy", "#Trending"]
            
            return result
            
        except Exception as e:
            logging.error(f"Manual parsing failed: {str(e)}")
            return None

    def process_single_article(self, article: Dict, emotions_list: List[str]) -> Optional[Dict]:
        """Process single article with Gemini API"""
        try:
            content = article.get('content', '')
            url = article.get('url', '')
            image_path = article.get('image_path')
            
            # Create comprehensive prompt using constants
            prompt = self.create_comprehensive_prompt(content, emotions_list)
            
            # Make API call
            response = self.safe_gemini_call(prompt)
            parsed_data = self.parse_gemini_response(response)
            
            if parsed_data:
                # Create final result with only required fields
                result = {
                    "title": article.get('title', 'Untitled'),
                    "category": parsed_data.get('category', 'entertainment'),
                    "description": parsed_data.get('description', ''),
                    "template_path": None,  # Will be filled by template manager
                    "image_path": image_path,
                    "dialogues": parsed_data.get('dialogues', []),
                    "hashtags": parsed_data.get('hashtags', []),
                    "source_url": url,
                    "emotion": parsed_data.get('emotion', '').lower()  # Needed for template matching
                }
                
                return result
            else:
                raise CustomException("Failed to parse Gemini response", sys)
        except CustomException:
            # Re-raise critical exceptions to stop the pipeline
            raise
        except Exception as e:
            clean_error = str(e).replace("ALTS creds ignored. Not running on GCP and untrusted ALTS is not enabled.", "").strip()
            logging.error(f"Error processing article: {clean_error}")
            return None

    def process_articles(self, categorized_articles: Dict[str, List[Dict]], emotions_list: List[str]) -> GeminiProcessorArtifact:
        """Process all articles with Gemini AI"""
        try:
            processed_content = []
            failed_articles = []
            total_api_calls = 0
            
            # Flatten articles for processing
            all_articles = []
            for category, articles in categorized_articles.items():
                for article in articles:
                    article['category'] = category # Ensure category is present
                    all_articles.append(article)
            
            total_articles = len(all_articles)
            logging.info(f"Processing {total_articles} articles with single Gemini API key")
            
            for i, article in enumerate(all_articles, 1):
                logging.info(f"Processing article {i}/{total_articles}: {article.get('title', 'No Title')}")
                
                try:
                    result = self.process_single_article(article, emotions_list)
                    total_api_calls += 1
                    
                    if result:
                        processed_content.append(result)
                        logging.info(f"SUCCESS! Article {i} processed")
                        # Log sample dialogue for verification
                        if result.get('dialogues'):
                            logging.info(f"  Sample dialogue: {result['dialogues'][0]}")
                    else:
                        failed_articles.append(article.get('source_url', f'article_{i}'))
                        logging.warning(f"FAILED to process article {i}")
                except CustomException as e:
                    # A critical error occurred (e.g., bad API key), stop processing.
                    logging.error(f"A critical error occurred while processing article {i}. Stopping pipeline.")
                    raise e
                except Exception as e:
                    total_api_calls += 1
                    failed_articles.append(article.get('source_url', f'article_{i}'))
                    clean_error = str(e).replace("ALTS creds ignored. Not running on GCP and untrusted ALTS is not enabled.", "").strip()
                    logging.error(f"An unexpected error occurred while processing article {i}: {clean_error}")
                    continue
                
                # Show progress
                success_rate = (len(processed_content) / i) * 100 if i > 0 else 0
                logging.info(f"Progress: {i}/{total_articles} | Success: {len(processed_content)} ({success_rate:.1f}%)")
            
            final_success_rate = (len(processed_content) / total_articles) * 100 if total_articles > 0 else 0
            
            logging.info(f"Gemini processing completed: {len(processed_content)}/{total_articles} articles processed ({final_success_rate:.1f}%)")
            
            return GeminiProcessorArtifact(
                processed_content=processed_content,
                total_api_calls=total_api_calls,
                success_rate=final_success_rate,
                failed_articles=failed_articles
            )
            
        except CustomException:
            # Re-raise to be caught by the main pipeline handler
            raise
        except Exception as e:
            logging.error(f"Error in process_articles: {str(e)}")
            raise CustomException(str(e), sys)









# import os
# import json
# import re
# import time
# import warnings
# import google.generativeai as genai
# import sys
# from typing import List, Dict, Optional
# from src.entity.artifacts import GeminiProcessorArtifact
# from src.entity.config_entity import GeminiProcessorConfig, ConfigEntity
# from src.logger import logging
# from src.exceptions import CustomException
# from src.utils.api_utils import APIKeyRotator, apply_rate_limiting
# from src.constants import GEMINI_COMPREHENSIVE_PROMPT

# # Suppress Google Cloud warnings
# os.environ['GRPC_VERBOSITY'] = 'ERROR'
# os.environ['GLOG_minloglevel'] = '2'
# warnings.filterwarnings("ignore", category=UserWarning, module="google.auth")

# class GeminiProcessor:
#     def __init__(self, api_keys: List[str]):
#         self.config = GeminiProcessorConfig(config=ConfigEntity())
        
#         # Filter out None values from API keys
#         valid_api_keys = [key for key in api_keys if key]
#         if not valid_api_keys:
#             raise CustomException("No valid Gemini API keys provided", sys)
        
#         # Initialize API key rotator
#         self.api_rotator = APIKeyRotator(
#             valid_api_keys, 
#             self.config.max_calls_per_key_per_minute
#         )
        
#         logging.info(f"GeminiProcessor initialized with {len(valid_api_keys)} API keys")

#     def create_comprehensive_prompt(self, news_content: str, emotions_list: List[str]) -> str:
#         """Create comprehensive prompt using template from constants"""
#         emotion_options = '\n'.join([f"- {emotion}" for emotion in emotions_list])
        
#         return GEMINI_COMPREHENSIVE_PROMPT.format(
#             news_content=news_content,
#             emotion_options=emotion_options
#         )

#     def safe_gemini_call(self, prompt: str) -> str:
#         """Make Gemini API call with proper key rotation and error handling"""
#         for attempt in range(self.config.max_gemini_retries):
#             try:
#                 key_index = self.api_rotator.get_next_available_key_index()
#                 api_key = self.api_rotator.get_api_key(key_index)
                
#                 logging.info(f"Using API Key #{key_index + 1}")
                
#                 # Configure Gemini with error suppression
#                 with warnings.catch_warnings():
#                     warnings.simplefilter("ignore")
#                     genai.configure(api_key=api_key)
#                     model = genai.GenerativeModel(self.config.gemini_model_name)
                
#                 # Record the call
#                 self.api_rotator.record_api_call(key_index)
                
#                 # Make the API call
#                 with warnings.catch_warnings():
#                     warnings.simplefilter("ignore")
#                     response = model.generate_content(prompt)
                
#                 # Apply rate limiting
#                 apply_rate_limiting(self.config.api_call_delay)
                
#                 return response.text.strip()
                
#             except Exception as e:
#                 error_msg = str(e)
#                 # Clean Google Cloud warnings from error message
#                 if "ALTS creds ignored" not in error_msg:
#                     logging.warning(f"API Key #{key_index + 1} failed: {error_msg}")
                
#                 if attempt < self.config.max_gemini_retries - 1:
#                     time.sleep(5)
#                 else:
#                     clean_error = error_msg.replace("ALTS creds ignored. Not running on GCP and untrusted ALTS is not enabled.", "").strip()
#                     raise CustomException(f"All API attempts failed: {clean_error}", sys)

#     def validate_and_fix_dialogues(self, dialogues: List[str]) -> List[str]:
#         """Validate and fix dialogue format to ensure they meet requirements"""
#         fixed_dialogues = []
        
#         for dialogue in dialogues[:2]:  # Only take first 2 dialogues
#             if isinstance(dialogue, str):
#                 # Split by newline to get lines
#                 lines = dialogue.split('\\n')
#                 if len(lines) < 2:
#                     lines = dialogue.split('\n')  # Try actual newline
                
#                 # Ensure we have exactly 2 lines
#                 if len(lines) >= 2:
#                     line1 = ' '.join(lines[0].strip().split()[:8])  # Max 8 words
#                     line2 = ' '.join(lines[1].strip().split()[:8])  # Max 8 words
                    
#                     if line1 and line2:  # Both lines have content
#                         fixed_dialogues.append(f"{line1}\\n{line2}")
#                     else:
#                         # Generate fallback if lines are empty
#                         fixed_dialogues.append("This news is so predictable\\nEveryone saw it coming already")
#                 else:
#                     # Single line dialogue - split into two parts
#                     words = dialogue.strip().split()
#                     if len(words) >= 4:
#                         mid = len(words) // 2
#                         line1 = ' '.join(words[:mid][:8])
#                         line2 = ' '.join(words[mid:][:8])
#                         fixed_dialogues.append(f"{line1}\\n{line2}")
#                     else:
#                         # Too short, create fallback
#                         fixed_dialogues.append("News like this be like\\nAbsolutely nobody is surprised today")
        
#         # Ensure we have exactly 2 dialogues
#         while len(fixed_dialogues) < 2:
#             fallback_dialogues = [
#                 "When news tries to shock us\\nBut we already knew everything",
#                 "Everyone after reading this news\\nNot surprised at all honestly"
#             ]
#             fixed_dialogues.append(fallback_dialogues[len(fixed_dialogues)])
        
#         return fixed_dialogues[:2]

#     def parse_gemini_response(self, response: str) -> Optional[Dict]:
#         """Parse JSON response from Gemini with proper dialogue validation"""
#         try:
#             # Try to extract JSON from response
#             json_pattern = r'\{.*?\}'
#             json_match = re.search(json_pattern, response, re.DOTALL)
            
#             if json_match:
#                 json_text = json_match.group(0)
#                 parsed = json.loads(json_text)
                
#                 required_fields = ['description', 'emotion', 'category', 'dialogues', 'hashtags']
#                 if all(key in parsed for key in required_fields):
#                     # Validate and fix dialogues
#                     if 'dialogues' in parsed and isinstance(parsed['dialogues'], list):
#                         parsed['dialogues'] = self.validate_and_fix_dialogues(parsed['dialogues'])
                    
#                     logging.info("Successfully parsed Gemini response")
#                     return parsed
                    
#             return self.manual_parse_response(response)
            
#         except json.JSONDecodeError:
#             return self.manual_parse_response(response)
#         except Exception as e:
#             logging.error(f"Error parsing Gemini response: {str(e)}")
#             return None

#     def manual_parse_response(self, response: str) -> Optional[Dict]:
#         """Manually parse response if JSON parsing fails"""
#         try:
#             result = {}
            
#             # Extract description
#             desc_patterns = [
#                 r'"?description"?\s*:\s*"([^"]+)"',
#                 r'description[:\s]+(.+?)(?=emotion|category|\n\n)',
#             ]
            
#             for pattern in desc_patterns:
#                 desc_match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
#                 if desc_match:
#                     result['description'] = desc_match.group(1).strip()
#                     break
            
#             if 'description' not in result:
#                 result['description'] = "Another predictable news story that surprises nobody\\nBecause apparently this passes for journalism\\nEveryone already knew this was coming"
            
#             # Extract emotion
#             emotion_match = re.search(r'"?emotion"?\s*:\s*"?(\w+)"?', response, re.IGNORECASE)
#             result['emotion'] = emotion_match.group(1).lower() if emotion_match else 'sarcasm'
            
#             # Extract category
#             category_match = re.search(r'"?category"?\s*:\s*"?(\w+)"?', response, re.IGNORECASE)
#             result['category'] = category_match.group(1) if category_match else 'entertainment'
            
#             # Generate natural fallback dialogues based on content
#             fallback_dialogues = [
#                 "When news tries to surprise us\\nBut everybody already knew this",
#                 "Me after reading this news\\nAbsolutely zero shock value here"
#             ]
            
#             # Try to extract dialogues from response
#             dialogue_quotes = re.findall(r'"([^"]+)"', response)
#             good_dialogues = []
            
#             for quote in dialogue_quotes:
#                 if 6 <= len(quote.split()) <= 16:  # Good length for 2-line dialogue
#                     good_dialogues.append(quote)
            
#             if len(good_dialogues) >= 2:
#                 result['dialogues'] = self.validate_and_fix_dialogues(good_dialogues[:2])
#             else:
#                 result['dialogues'] = fallback_dialogues
            
#             # Extract hashtags
#             hashtags = re.findall(r'#\w+', response)
#             if len(hashtags) >= 4:
#                 result['hashtags'] = hashtags[:8]
#             else:
#                 result['hashtags'] = ["#SavageNews", "#MemeWorthy", "#ViralContent", "#Sarcasm", "#Buzzy", "#Trending"]
            
#             return result
            
#         except Exception as e:
#             logging.error(f"Manual parsing failed: {str(e)}")
#             return None

#     def process_single_article(self, article: Dict, emotions_list: List[str]) -> Optional[Dict]:
#         """Process single article with Gemini API"""
#         try:
#             content = article.get('content', '')
#             url = article.get('url', '')
#             image_path = article.get('image_path')
            
#             # Create comprehensive prompt using constants
#             prompt = self.create_comprehensive_prompt(content, emotions_list)
            
#             # Make API call
#             response = self.safe_gemini_call(prompt)
#             parsed_data = self.parse_gemini_response(response)
            
#             if parsed_data:
#                 # Create final result with only required fields
#                 result = {
#                     "category": parsed_data.get('category', 'entertainment'),
#                     "description": parsed_data.get('description', ''),
#                     "template_path": None,  # Will be filled by template manager
#                     "image_path": image_path,
#                     "dialogues": parsed_data.get('dialogues', []),
#                     "hashtags": parsed_data.get('hashtags', []),
#                     "url": url,
#                     "emotion": parsed_data.get('emotion', '').lower()  # Needed for template matching
#                 }
                
#                 return result
#             else:
#                 raise CustomException("Failed to parse Gemini response", sys)
                
#         except Exception as e:
#             clean_error = str(e).replace("ALTS creds ignored. Not running on GCP and untrusted ALTS is not enabled.", "").strip()
#             logging.error(f"Error processing article: {clean_error}")
#             return None

#     def process_articles(self, categorized_articles: Dict[str, List[Dict]], emotions_list: List[str]) -> GeminiProcessorArtifact:
#         """Process all articles with Gemini AI"""
#         try:
#             processed_content = []
#             failed_articles = []
#             total_api_calls = 0
            
#             # Flatten articles for processing
#             all_articles = []
#             for category, articles in categorized_articles.items():
#                 all_articles.extend(articles)
            
#             total_articles = len(all_articles)
#             logging.info(f"Processing {total_articles} articles with Gemini AI")
            
#             for i, article in enumerate(all_articles, 1):
#                 logging.info(f"Processing article {i}/{total_articles}")
                
#                 try:
#                     result = self.process_single_article(article, emotions_list)
#                     total_api_calls += 1
                    
#                     if result:
#                         processed_content.append(result)
#                         logging.info(f"SUCCESS! Article {i} processed")
#                         # Log sample dialogue for verification
#                         if result.get('dialogues'):
#                             logging.info(f"  Sample dialogue: {result['dialogues'][0]}")
#                     else:
#                         failed_articles.append(article.get('url', f'article_{i}'))
#                         logging.warning(f"FAILED to process article {i}")
                        
#                 except Exception as e:
#                     total_api_calls += 1
#                     failed_articles.append(article.get('url', f'article_{i}'))
#                     clean_error = str(e).replace("ALTS creds ignored. Not running on GCP and untrusted ALTS is not enabled.", "").strip()
#                     logging.error(f"Error processing article {i}: {clean_error}")
#                     continue
                
#                 # Show progress
#                 success_rate = (len(processed_content) / i) * 100 if i > 0 else 0
#                 logging.info(f"Progress: {i}/{total_articles} | Success: {len(processed_content)} ({success_rate:.1f}%)")
            
#             final_success_rate = (len(processed_content) / total_articles) * 100 if total_articles > 0 else 0
            
#             logging.info(f"Gemini processing completed: {len(processed_content)}/{total_articles} articles processed ({final_success_rate:.1f}%)")
            
#             return GeminiProcessorArtifact(
#                 processed_content=processed_content,
#                 total_api_calls=total_api_calls,
#                 success_rate=final_success_rate,
#                 failed_articles=failed_articles
#             )
            
#         except Exception as e:
#             logging.error(f"Error in process_articles: {str(e)}")
#             raise CustomException(e, sys)


