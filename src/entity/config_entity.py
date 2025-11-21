from src.constants import *
import os
from typing import List, Dict, Any

class ConfigEntity:
    def __init__(self):
        # Directory configuration
        self.output_dir = OUTPUT_DIR
        self.images_dir = IMAGES_DIR
        self.logs_dir = LOGS_DIR
        
        # File naming
        self.news_data_prefix = NEWS_DATA_PREFIX
        self.processed_memes_prefix = PROCESSED_MEMES_PREFIX
        self.json_extension = JSON_EXTENSION
        self.image_extensions = IMAGE_EXTENSIONS
        
        # News extraction
        self.target_categories = TARGET_CATEGORIES
        self.articles_per_category = ARTICLES_PER_CATEGORY
        self.max_articles_per_source = MAX_ARTICLES_PER_SOURCE
        self.min_title_length = MIN_TITLE_LENGTH
        self.min_content_length = MIN_CONTENT_LENGTH
        
        # Scraping configuration
        self.request_timeout = REQUEST_TIMEOUT
        self.scraping_delay_min = SCRAPING_DELAY_MIN
        self.scraping_delay_max = SCRAPING_DELAY_MAX
        self.max_retries = MAX_RETRIES
        self.default_headers = DEFAULT_HEADERS
        self.news_sources = NEWS_SOURCES
        
        # Buzz scoring
        self.high_buzz_words = HIGH_BUZZ_WORDS
        self.category_buzz_words = CATEGORY_BUZZ_WORDS
        self.base_buzz_score = BASE_BUZZ_SCORE
        self.max_buzz_score = MAX_BUZZ_SCORE
        self.content_length_bonus_threshold_1 = CONTENT_LENGTH_BONUS_THRESHOLD_1
        self.content_length_bonus_threshold_2 = CONTENT_LENGTH_BONUS_THRESHOLD_2
        self.title_length_bonus_threshold = TITLE_LENGTH_BONUS_THRESHOLD
        
        # Category classification
        self.category_keywords = CATEGORY_KEYWORDS
        
        # Image processing
        self.min_image_size_bytes = MIN_IMAGE_SIZE_BYTES
        self.valid_image_extensions = VALID_IMAGE_EXTENSIONS
        self.skip_image_patterns = SKIP_IMAGE_PATTERNS
        
        # Gemini API
        self.gemini_model_name = GEMINI_MODEL_NAME
        self.max_calls_per_key_per_minute = MAX_CALLS_PER_KEY_PER_MINUTE
        self.api_call_delay = API_CALL_DELAY
        self.gemini_request_timeout = GEMINI_REQUEST_TIMEOUT
        self.max_gemini_retries = MAX_GEMINI_RETRIES
        
        # Supabase
        self.supabase_schema = SUPABASE_SCHEMA
        self.emotions_table = EMOTIONS_TABLE
        self.memes_table = MEMES_TABLE
        self.similarity_threshold = SIMILARITY_THRESHOLD
        self.supabase_image_base_url = SUPABASE_IMAGE_BASE_URL  # ADD THIS LINE
        
        # Content processing
        self.duplicate_content_hash_length = DUPLICATE_CONTENT_HASH_LENGTH
        self.max_content_parts = MAX_CONTENT_PARTS
        self.max_content_length = MAX_CONTENT_LENGTH
        
        # Meme Generation
        self.meme_template_width = MEME_TEMPLATE_WIDTH
        self.meme_template_height = MEME_TEMPLATE_HEIGHT
        self.meme_max_font_size = MEME_MAX_FONT_SIZE
        self.meme_min_font_size = MEME_MIN_FONT_SIZE
        self.meme_text_padding = MEME_TEXT_PADDING
        self.meme_outline_width = MEME_OUTLINE_WIDTH
        self.meme_line_spacing = MEME_LINE_SPACING
        self.font_paths = FONT_PATHS
        self.meme_text_color = MEME_TEXT_COLOR
        self.meme_outline_color = MEME_OUTLINE_COLOR

class NewsExtractorConfig:
    def __init__(self, config: ConfigEntity):
        self.output_dir = config.output_dir
        self.target_categories = config.target_categories
        self.max_articles_per_source = config.max_articles_per_source
        self.min_title_length = config.min_title_length
        self.min_content_length = config.min_content_length
        self.request_timeout = config.request_timeout
        self.scraping_delay_min = config.scraping_delay_min
        self.scraping_delay_max = config.scraping_delay_max
        self.max_retries = config.max_retries
        self.default_headers = config.default_headers
        self.news_sources = config.news_sources
        self.max_content_parts = config.max_content_parts

class ContentProcessorConfig:
    def __init__(self, config: ConfigEntity):
        self.target_categories = config.target_categories
        self.articles_per_category = config.articles_per_category
        self.high_buzz_words = config.high_buzz_words
        self.category_buzz_words = config.category_buzz_words
        self.base_buzz_score = config.base_buzz_score
        self.max_buzz_score = config.max_buzz_score
        self.content_length_bonus_threshold_1 = config.content_length_bonus_threshold_1
        self.content_length_bonus_threshold_2 = config.content_length_bonus_threshold_2
        self.title_length_bonus_threshold = config.title_length_bonus_threshold
        self.category_keywords = config.category_keywords
        self.duplicate_content_hash_length = config.duplicate_content_hash_length

class ImageDownloaderConfig:
    def __init__(self, config: ConfigEntity):
        self.output_dir = config.output_dir
        self.images_dir = config.images_dir
        self.min_image_size_bytes = config.min_image_size_bytes
        self.valid_image_extensions = config.valid_image_extensions
        self.skip_image_patterns = config.skip_image_patterns
        self.request_timeout = config.request_timeout
        self.default_headers = config.default_headers

class GeminiProcessorConfig:
    def __init__(self, config: ConfigEntity):
        self.gemini_model_name = config.gemini_model_name
        self.max_calls_per_key_per_minute = config.max_calls_per_key_per_minute
        self.api_call_delay = config.api_call_delay
        self.gemini_request_timeout = config.gemini_request_timeout
        self.max_gemini_retries = config.max_gemini_retries

class TemplateManagerConfig:
    def __init__(self, config: ConfigEntity):
        self.supabase_schema = config.supabase_schema
        self.emotions_table = config.emotions_table
        self.memes_table = config.memes_table
        self.similarity_threshold = config.similarity_threshold
        self.supabase_image_base_url = config.supabase_image_base_url  # ADD THIS LINE

class OutputManagerConfig:
    def __init__(self, config: ConfigEntity):
        self.output_dir = config.output_dir
        self.news_data_prefix = config.news_data_prefix
        self.processed_memes_prefix = config.processed_memes_prefix
        self.json_extension = config.json_extension
        self.target_categories = config.target_categories

class MemeGeneratorConfig:
    def __init__(self, config: ConfigEntity):
        self.template_width = config.meme_template_width
        self.template_height = config.meme_template_height
        self.max_font_size = config.meme_max_font_size
        self.min_font_size = config.meme_min_font_size
        self.text_padding = config.meme_text_padding
        self.outline_width = config.meme_outline_width
        self.line_spacing = config.meme_line_spacing
        self.font_paths = config.font_paths
        self.text_color = config.meme_text_color
        self.outline_color = config.meme_outline_color