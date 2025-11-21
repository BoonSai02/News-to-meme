from supabase import Client
from typing import Dict, List, Optional
import sys
import requests
from src.logger import logging
from src.exceptions import CustomException


def load_emotions_from_database(supabase_client: Client, schema: str, table: str) -> Dict[str, Dict]:
    """Load emotions from Supabase database - using Accept-Profile headers"""
    try:
        logging.info(f"Loading emotions from table '{table}' in schema '{schema}'")
        
        # Ensure headers are set for schema access
        supabase_client.postgrest.session.headers.update({'Accept-Profile': schema})
        
        # Simple table access - schema configured via headers
        response = supabase_client.table(table).select("*").execute()
        
        if response.data:
            emotions_dict = {}
            for emotion in response.data:
                emotion_label = emotion['emotion_label'].lower()
                emotions_dict[emotion_label] = {
                    'emotion_id': emotion['emotion_id'],  # This is UUID
                    'emotion_label': emotion['emotion_label'],
                    'description': emotion['description']
                }
            
            logging.info(f"Successfully loaded {len(emotions_dict)} emotions from {schema}.{table}")
            logging.info(f"Available emotions: {list(emotions_dict.keys())}")
            return emotions_dict
        else:
            logging.warning("No emotions found in database")
            return {}
            
    except Exception as e:
        logging.error(f"Error loading emotions from {schema}.{table}: {str(e)}")
        return {}


def get_template_by_emotion_id(supabase_client: Client, schema: str, table: str, emotion_id: str) -> Optional[str]:
    """Get meme template path by emotion ID (UUID) - using Accept-Profile headers"""
    try:
        logging.info(f"Searching for templates with emotion_id: {emotion_id} in {schema}.{table}")
        
        # Ensure headers are set for schema access
        supabase_client.postgrest.session.headers.update({'Accept-Profile': schema})
        
        # Simple table access - schema configured via headers
        response = supabase_client.table(table).select("*").eq('emotion_id', emotion_id).execute()
        
        if response.data:
            logging.info(f"Found {len(response.data)} templates for emotion_id: {emotion_id}")
            
            # Log all available templates
            for i, template in enumerate(response.data):
                meme_id = template.get('meme_id', 'NO_ID')
                image_path = template.get('image_path', '')
                logging.info(f"  Template {i+1}: meme_id={meme_id}, image_path={image_path[:50]}...")
            
            # Select random template
            import random
            selected_template = random.choice(response.data)
            
            # Get the image path
            image_path = selected_template.get('image_path', '')
            
            if image_path:
                logging.info(f"Selected template for emotion_id {emotion_id}: {image_path[:50]}...")
                return image_path
            else:
                logging.warning(f"Template found but no image_path for emotion_id {emotion_id}")
                return None
        else:
            logging.warning(f"No templates found for emotion_id: {emotion_id}")
            return None
        
    except Exception as e:
        logging.error(f"Error getting template for emotion_id {emotion_id}: {str(e)}")
        return None


def get_random_template(supabase_client: Client, schema: str, table: str) -> Optional[str]:
    """Get random meme template path - using Accept-Profile headers"""
    try:
        logging.info(f"Getting random template from {schema}.{table}")
        
        # Ensure headers are set for schema access
        supabase_client.postgrest.session.headers.update({'Accept-Profile': schema})
        
        # Simple table access - schema configured via headers
        response = supabase_client.table(table).select("*").limit(10).execute()
        
        if response.data:
            import random
            selected_template = random.choice(response.data)
            
            # Get the image path
            image_path = selected_template.get('image_path', '')
            
            if image_path:
                logging.info(f"Selected random template: {image_path[:50]}...")
                return image_path
            else:
                logging.warning("Random template found but no image_path")
                return None
        else:
            logging.warning("No templates found for random selection")
            return None
        
    except Exception as e:
        logging.error(f"Error getting random template: {str(e)}")
        return None


def download_template_from_url(base_url: str, image_path: str, timeout: int = 10) -> Optional[bytes]:
    """Download template image from Supabase URL"""
    try:
        # The image_path contains the storage path like: "storage/v1/object/public/meta-data/mem..."
        
        # Construct full URL
        if image_path.startswith('storage/'):
            # Full path from Supabase storage
            if base_url.endswith('/'):
                base_url = base_url.rstrip('/')
            full_url = f"{base_url}/{image_path}"
        else:
            # Regular path concatenation
            if not base_url.endswith('/'):
                base_url += '/'
            full_url = base_url + image_path.lstrip('/')
        
        logging.info(f"Downloading template from: {full_url[:100]}...")
        
        # Download the image
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(full_url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        if len(response.content) > 1000:  # Basic validation - should be larger than 1KB
            logging.info(f"Successfully downloaded template: {len(response.content)} bytes")
            return response.content
        else:
            logging.warning(f"Downloaded template too small: {len(response.content)} bytes")
            return None
            
    except requests.RequestException as e:
        logging.error(f"Error downloading template from URL: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error downloading template: {str(e)}")
        return None


def test_schema_access(supabase_client: Client, schema: str = 'dc'):
    """Test access to tables - using Accept-Profile headers"""
    try:
        logging.info(f"Testing {schema} schema access with Accept-Profile headers")
        
        # Set headers for schema access
        supabase_client.postgrest.session.headers.update({'Accept-Profile': schema})
        
        # Test emotions table
        try:
            response = supabase_client.table('emotions').select("*").limit(1).execute()
            logging.info(f"{schema}.emotions table accessible: {len(response.data)} records found")
            if response.data:
                sample = response.data[0]
                logging.info(f"Sample emotion: {sample['emotion_label']} - {sample['emotion_id']}")
        except Exception as e:
            logging.error(f"{schema}.emotions table not accessible: {str(e)}")
        
        # Test memes_dc table
        try:
            response = supabase_client.table('memes_dc').select("*").limit(1).execute()
            logging.info(f"{schema}.memes_dc table accessible: {len(response.data)} records found")
            if response.data:
                sample_meme = response.data[0]
                image_path = sample_meme.get('image_path', '')
                logging.info(f"Sample meme: meme_id={sample_meme.get('meme_id', 'NO_ID')}, image_path={image_path[:50]}...")
        except Exception as e:
            logging.error(f"{schema}.memes_dc table not accessible: {str(e)}")
            
    except Exception as e:
        logging.error(f"Error in {schema} schema access test: {str(e)}")






















# from supabase import Client
# from typing import Dict, List, Optional
# import sys
# from src.logger import logging
# from src.exceptions import CustomException

# def load_emotions_from_database(supabase_client: Client, schema: str, table: str) -> Dict[str, Dict]:
#     """Load emotions from Supabase database"""
#     try:
#         logging.info(f"Loading emotions from Supabase table: {table}")
        
#         # For Supabase, if using a schema other than 'public', table should already include schema
#         # If table already has schema prefix, use as-is, otherwise just use table name
#         if '.' in table:
#             # Table already has schema prefix
#             response = supabase_client.from_(table).select('*').execute()
#         else:
#             # Just table name, let Supabase handle default schema
#             response = supabase_client.from_(table).select('*').execute()
        
#         if response.data:
#             emotions_dict = {}
#             for emotion in response.data:
#                 emotion_label = emotion['emotion_label'].lower()
#                 emotions_dict[emotion_label] = {
#                     'emotion_id': emotion['emotion_id'],
#                     'emotion_label': emotion['emotion_label'],
#                     'description': emotion['description']
#                 }
            
#             logging.info(f"Loaded {len(emotions_dict)} emotions from database")
#             return emotions_dict
#         else:
#             logging.warning("No emotions found in database")
#             return {}
            
#     except Exception as e:
#         logging.error(f"Error loading emotions from {table}: {str(e)}")
#         # Return empty dict instead of raising exception for now
#         return {}

# def get_template_by_emotion_id(supabase_client: Client, schema: str, table: str, 
#                               emotion_id: int) -> Optional[str]:
#     """Get meme template by emotion ID"""
#     try:
#         logging.info(f"Getting template for emotion_id {emotion_id} from table: {table}")
        
#         # Handle schema the same way
#         if '.' in table:
#             response = supabase_client.from_(table).select('*').eq('emotion_id', emotion_id).execute()
#         else:
#             response = supabase_client.from_(table).select('*').eq('emotion_id', emotion_id).execute()
        
#         if response.data:
#             import random
#             selected_template = random.choice(response.data)
#             return selected_template.get('image_path', '')
#         return None
        
#     except Exception as e:
#         logging.error(f"Error getting template for emotion_id {emotion_id}: {str(e)}")
#         return None

# def get_random_template(supabase_client: Client, schema: str, table: str) -> Optional[str]:
#     """Get random meme template when emotion matching fails"""
#     try:
#         logging.info(f"Getting random template from table: {table}")
        
#         # Handle schema the same way
#         if '.' in table:
#             response = supabase_client.from_(table).select('*').limit(10).execute()
#         else:
#             response = supabase_client.from_(table).select('*').limit(10).execute()
        
#         if response.data:
#             import random
#             selected_template = random.choice(response.data)
#             return selected_template.get('image_path', '')
#         return None
        
#     except Exception as e:
#         logging.error(f"Error getting random template: {str(e)}")
#         return None




