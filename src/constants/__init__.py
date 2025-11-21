# Constants for News Meme Generation Pipeline

import random
import os

# Directory structure
OUTPUT_DIR = "artifacts"
IMAGES_DIR = "images"
LOGS_DIR = "logs"

# File naming patterns
NEWS_DATA_PREFIX = "news_data"
PROCESSED_MEMES_PREFIX = "sarcastic_news_memes"
JSON_EXTENSION = ".json"
IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"]

# News extraction constants
TARGET_CATEGORIES = ['politics', 'movies', 'entertainment', 'sports', 'business', 'technology']
ARTICLES_PER_CATEGORY = 1
MAX_ARTICLES_PER_SOURCE = 2
MIN_TITLE_LENGTH = 10
MIN_CONTENT_LENGTH = 15

# Scraping configuration
REQUEST_TIMEOUT = 15
SCRAPING_DELAY_MIN = 0.3
SCRAPING_DELAY_MAX = 0.8
MAX_RETRIES = 3

# Headers for web requests
def get_random_user_agent():
    return f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(90, 120)}.0.0.0 Safari/537.36'

DEFAULT_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}

NEWS_SOURCES = {
    # MAJOR TELUGU NEWS CHANNELS - Verified Working & Scraping-Friendly
    'sakshi_main': {'url': 'https://www.sakshi.com/', 'selectors': ['h3 a', 'h2 a', '.news-title a', '.story-card h3 a'], 'category': 'politics'},
    'eenadu_main': {'url': 'https://www.eenadu.net/', 'selectors': ['h3 a', 'h2 a', '.story-title a', '.news-headline a'], 'category': 'politics'},
    'andhrajyothy_main': {'url': 'https://www.andhrajyothy.com/', 'selectors': ['h3 a', 'h2 a', '.news-title a', '.article-title a'], 'category': 'politics'},
    'ntv_telugu': {'url': 'https://ntvtelugu.com/', 'selectors': ['h3 a', 'h2 a', '.news-item h3 a', '.story-headline a'], 'category': 'entertainment'},
    
    # VERIFIED SCRAPING-FRIENDLY TELUGU PORTALS
    'v6_news': {'url': 'https://www.v6velugu.com/', 'selectors': ['h3 a', 'h2 a', '.story-card h3 a', '.news-title a'], 'category': 'entertainment'},
    'greatandhra': {'url': 'https://www.greatandhra.com/', 'selectors': ['h3 a', 'h2 a', '.post-title a', '.news-item h3 a'], 'category': 'movies'},
    'gulte_main': {'url': 'https://www.gulte.com/', 'selectors': ['h3 a', 'h2 a', '.post-title a', '.story-title a'], 'category': 'movies'},
    'tv5_news': {'url': 'https://www.tv5news.in/', 'selectors': ['h3 a', 'h2 a', '.news-headline a', '.article-title a'], 'category': 'entertainment'},
    
    # REGIONAL FOCUS - AP & TELANGANA
    'namasthe_telangana': {'url': 'https://www.ntnews.com/', 'selectors': ['h3 a', 'h2 a', '.story-card h3 a'], 'category': 'politics'},
    'mana_telangana': {'url': 'https://manatelangana.news/', 'selectors': ['h3 a', 'h2 a', '.news-title a'], 'category': 'politics'},
    'telugu_bullet': {'url': 'https://telugu.telugubullet.com/', 'selectors': ['h3 a', 'h2 a', '.post-title a'], 'category': 'entertainment'},
    'visala_andhra': {'url': 'https://www.visalaandhra.com/', 'selectors': ['h3 a', 'h2 a', '.story-headline a'], 'category': 'entertainment'},
    
    # ENTERTAINMENT & MOVIE NEWS - High Engagement
    'tupaki_main': {'url': 'https://www.tupaki.com/', 'selectors': ['h3 a', 'h2 a', '.news-item h3 a'], 'category': 'movies'},
    'telugu360': {'url': 'https://www.telugu360.com/', 'selectors': ['h3 a', 'h2 a', '.post-title a'], 'category': 'movies'},
    'teluguone': {'url': 'https://www.teluguone.com/news/', 'selectors': ['h3 a', 'h2 a', '.story-title a'], 'category': 'movies'},
    'oneindia_telugu': {'url': 'https://telugu.oneindia.com/', 'selectors': ['h3 a', 'h2 a', '.story-card h3 a'], 'category': 'entertainment'},
    
    # SPORTS NEWS IN TELUGU
    'sakshi_sports': {'url': 'https://www.sakshi.com/sports', 'selectors': ['h3 a', 'h2 a'], 'category': 'sports'},
    'eenadu_sports': {'url': 'https://www.eenadu.net/sports', 'selectors': ['h3 a', 'h2 a'], 'category': 'sports'},
    'v6_sports': {'url': 'https://www.v6velugu.com/sports', 'selectors': ['h3 a', 'h2 a'], 'category': 'sports'},
    
    # BUSINESS & TECHNOLOGY IN TELUGU
    'sakshi_business': {'url': 'https://www.sakshi.com/business', 'selectors': ['h3 a', 'h2 a'], 'category': 'business'},
    'eenadu_business': {'url': 'https://www.eenadu.net/business', 'selectors': ['h3 a', 'h2 a'], 'category': 'business'},
    'ntv_tech': {'url': 'https://ntvtelugu.com/technology', 'selectors': ['h3 a', 'h2 a'], 'category': 'technology'},
}
# # News sources configuration
# NEWS_SOURCES = {
#     # POLITICS SOURCES - Top 3
#     'ie_politics': {'url': 'https://indianexpress.com/section/political-pulse/', 'selectors': ['h3 a', 'h2 a'], 'category': 'politics'},
#     'toi_politics': {'url': 'https://timesofindia.indiatimes.com/india', 'selectors': ['a[href*="/articleshow/"]', 'h3 a'], 'category': 'politics'},
#     'ht_politics': {'url': 'https://www.hindustantimes.com/india-news', 'selectors': ['h3 a', 'h2 a'], 'category': 'politics'},

#     # ENTERTAINMENT & MOVIES SOURCES - Top 3
#     'toi_movies': {'url': 'https://timesofindia.indiatimes.com/entertainment/hindi/bollywood/news', 'selectors': ['a[href*="/articleshow/"]', 'h3 a'], 'category': 'movies'},
#     'news18_entertainment': {'url': 'https://www.news18.com/entertainment/', 'selectors': ['h3 a', 'h2 a'], 'category': 'entertainment'},
#     'indiatoday_entertainment': {'url': 'https://www.indiatoday.in/movies', 'selectors': ['h2 a', 'h3 a'], 'category': 'entertainment'},

#     # SPORTS SOURCES - Top 3
#     'toi_sports': {'url': 'https://timesofindia.indiatimes.com/sports', 'selectors': ['a[href*="/articleshow/"]', 'h3 a'], 'category': 'sports'},
#     'ht_sports': {'url': 'https://www.hindustantimes.com/sports', 'selectors': ['h3 a', 'h2 a'], 'category': 'sports'},
#     'indiatoday_sports': {'url': 'https://www.indiatoday.in/sports', 'selectors': ['h2 a', 'h3 a'], 'category': 'sports'},

#     # BUSINESS SOURCES - Top 3
#     'economic_times': {'url': 'https://economictimes.indiatimes.com/', 'selectors': ['h3 a', 'h2 a'], 'category': 'business'},
#     'livemint': {'url': 'https://www.livemint.com/', 'selectors': ['h3 a', 'h2 a'], 'category': 'business'},
#     'moneycontrol': {'url': 'https://www.moneycontrol.com/news/', 'selectors': ['h3 a', 'h2 a'], 'category': 'business'},

#     # TECHNOLOGY SOURCES - Top 3
#     'toi_technology': {'url': 'https://timesofindia.indiatimes.com/gadgets-news', 'selectors': ['a[href*="/articleshow/"]', 'h3 a'], 'category': 'technology'},
#     'et_tech': {'url': 'https://economictimes.indiatimes.com/tech', 'selectors': ['h3 a', 'h2 a'], 'category': 'technology'},
#     'indiatoday_tech': {'url': 'https://www.indiatoday.in/technology/news', 'selectors': ['h2 a', 'h3 a'], 'category': 'technology'},

#     # TRENDING / VIRAL SOURCES - Top 3
#     'ht_trending': {'url': 'https://www.hindustantimes.com/trending', 'selectors': ['h3 a', 'h2 a'], 'category': 'trending'},
#     'indianexpress_trending': {'url': 'https://indianexpress.com/section/trending/', 'selectors': ['h3 a', 'h2 a'], 'category': 'trending'},
#     'indiatoday_trending': {'url': 'https://www.indiatoday.in/trending-news', 'selectors': ['h2 a', 'h3 a'], 'category': 'trending'},
# }


# Enhanced Telugu Buzz Score Keywords  
HIGH_BUZZ_WORDS = {
    # Original English keywords
    'breaking': 4, 'exclusive': 3, 'shocking': 3, 'controversy': 3,
    'scandal': 3, 'arrest': 2, 'murder': 3, 'viral': 3,
    'trending': 2, 'major': 2, 'important': 2, 'crisis': 2,
    'emergency': 2, 'urgent': 2, 'alert': 2, 'warning': 1,
    'wins': 2, 'loses': 1, 'victory': 2, 'defeat': 1, 'new': 1,
    
    # Telugu script keywords
    'బ్రేకింగ్': 4, 'ఎక్స్‌క్లూసివ్': 3, 'షాకింగ్': 3, 'వివాదాస్పదం': 3,
    'కుంభకోణం': 3, 'అరెస్ట్': 2, 'హత్య': 3, 'వైరల్': 3,
    'ట్రెండింగ్': 2, 'మేజర్': 2, 'ప్రధానం': 2, 'సంక్షోభం': 2,
    'అత్యవసరం': 2, 'అర్జెంట్': 2, 'హెచ్చరిక': 2, 'హెచ్చరిక': 1,
    'గెలుపు': 2, 'ఓటమి': 1, 'విజయం': 2, 'పరాజయం': 1, 'కొత్త': 1,
    
    # Transliterated Telugu (Tnglish)
    'breakingu': 4, 'exclusivu': 3, 'shockingu': 3, 'controversyu': 3,
    'kumbhakonam': 3, 'arrestu': 2, 'hatyaa': 3, 'viralu': 3,
    'trendingu': 2, 'majoru': 2, 'pradhanam': 2, 'sankshobham': 2,
    'atyavasaram': 2, 'urgentu': 2, 'hecharika': 2, 'warningu': 1,
    'gelupu': 2, 'otami': 1, 'vijayam': 2, 'paraajayam': 1, 'kotha': 1,
    
    # High-engagement Telugu words
    'సంచలనం': 3, 'భయంకరం': 3, 'ఘోరం': 4, 'మహా': 2, 'భారీ': 2,
    'పేలుడుకర': 4, 'రహస్యం': 3, 'లీక్': 4, 'దాచిన': 3, 'లోపలి': 3,
    'విపత్తు': 3, 'ముప్పు': 2, 'ప్రమాదం': 3, 'భయం': 2, 'అవినీతి': 4,
    'లంచం': 3, 'కోట్లు': 3, 'లక్షలు': 2, 'నిరసన': 2, 'సమ్మె': 2,
    'హాట్': 3, 'హిట్': 2, 'సెన్సేషన్': 3, 'బోంబ్': 4, 'ఫైర్': 3
}

CATEGORY_BUZZ_WORDS = {
    # Original English keywords
    'bollywood': 2, 'cricket': 2, 'election': 2, 'politics': 1,
    'technology': 1, 'business': 1, 'sports': 1, 'movie': 1,
    'celebrity': 1, 'actor': 1, 'match': 1, 'win': 1, 'lose': 1,
    'ipl': 2, 'box office': 2, 'release': 1, 'hit': 1, 'flop': 1,
    'update': 1, 'news': 1, 'latest': 1, 'today': 1,
    
    # Telugu script category keywords
    'బాలీవుడ్': 2, 'క్రికెట్': 2, 'ఎన్నికలు': 2, 'రాజకీయాలు': 1,
    'సాంకేతికత': 1, 'వ్యాపారం': 1, 'క్రీడలు': 1, 'మూవీ': 1,
    'సెలబ్రిటీ': 1, 'నటుడు': 1, 'మ్యాచ్': 1, 'గెలుపు': 1, 'ఓటమి': 1,
    'ఐపీఎల్': 2, 'బాక్స్ ఆఫీస్': 2, 'రిలీజ్': 1, 'హిట్': 1, 'ఫ్లాప్': 1,
    'అప్డేట్': 1, 'వార్తలు': 1, 'లేటెస్ట్': 1, 'ఈరోజు': 1,
    
    # Transliterated Telugu category keywords  
    'bollywoodu': 2, 'cricketu': 2, 'ennikalu': 2, 'rajakiyaalu': 1,
    'technologyu': 1, 'vyapaaram': 1, 'kreedalu': 1, 'cinemaa': 1,
    'celebrityu': 1, 'natudu': 1, 'matchu': 1, 'winu': 1, 'loseu': 1,
    'iplu': 2, 'boxofficeu': 2, 'releaseu': 1, 'hitu': 1, 'flapu': 1,
    'updateu': 1, 'newsulu': 1, 'latestu': 1, 'todayu': 1,
    
    # High-engagement Telugu category words
    'టాలీవుడ్': 3, 'సినిమా': 2, 'చిత్రం': 2, 'హీరో': 2, 'హీరోయిన్': 2,
    'దర్శకుడు': 1, 'నిర్మాత': 1, 'పాట': 2, 'సంగీతం': 2, 'కథ': 1,
    'ప్రభుత్వం': 1, 'మంత్రి': 2, 'నాయకుడు': 1, 'పార్టీ': 1, 'అభ్యర్థి': 1,
    'ఓటు': 1, 'ప్రచారం': 1, 'అసెంబ్లీ': 1, 'పార్లమెంట్': 1, 'సర్కార్': 1,
    'టీమ్': 1, 'ఆటగాడు': 1, 'కెప్టెన్': 1, 'కోచ్': 1, 'టోర్నమెంట్': 1,
    'రికార్డు': 2, 'ఛాంపియన్': 2, 'స్కోరు': 1, 'గోల్': 1, 'ప్రదర్శన': 1,
    'కంపెనీ': 1, 'మార్కెట్': 1, 'స్టాక్': 1, 'ధర': 1, 'లాభం': 1,
    'నష్టం': 1, 'పెట్టుబడి': 1, 'బ్యాంకు': 1, 'రుణం': 1, 'వడ్డీ': 1,
    'మొబైల్': 1, 'ఇంటర్నెట్': 1, 'కంప్యూటర్': 1, 'యాప్': 1, 'డిజిటల్': 1,
    'ఆన్‌లైన్': 1, 'సాఫ్ట్‌వేర్': 1, 'టెక్నాలజీ': 1, 'ఆర్టిఫిషియల్': 2
}
# # Buzz score keywords
# HIGH_BUZZ_WORDS = {
#     'breaking': 4, 'exclusive': 3, 'shocking': 3, 'controversy': 3,
#     'scandal': 3, 'arrest': 2, 'murder': 3, 'viral': 3,
#     'trending': 2, 'major': 2, 'important': 2, 'crisis': 2,
#     'emergency': 2, 'urgent': 2, 'alert': 2, 'warning': 1,
#     'wins': 2, 'loses': 1, 'victory': 2, 'defeat': 1, 'new': 1
# }

# CATEGORY_BUZZ_WORDS = {
#     'bollywood': 2, 'cricket': 2, 'election': 2, 'politics': 1,
#     'technology': 1, 'business': 1, 'sports': 1, 'movie': 1,
#     'celebrity': 1, 'actor': 1, 'match': 1, 'win': 1, 'lose': 1,
#     'ipl': 2, 'box office': 2, 'release': 1, 'hit': 1, 'flop': 1,
#     'update': 1, 'news': 1, 'latest': 1, 'today': 1
# }

# Category classification keywords
CATEGORY_KEYWORDS = {
    'politics': ['election', 'parliament', 'minister', 'government', 'political', 'bjp', 'congress', 'modi', 'politics', 'vote', 'party', 'constituency', 'leader', 'pm', 'chief minister'],
    'movies': ['movie', 'film', 'actor', 'actress', 'bollywood', 'cinema', 'box office', 'trailer', 'director', 'producer', 'release', 'star', 'role', 'shoot', 'debut'],
    'entertainment': ['entertainment', 'celebrity', 'music', 'tv show', 'award', 'concert', 'performance', 'artist', 'singer', 'album', 'show', 'reality', 'dance', 'talent'],
    'sports': ['cricket', 'football', 'sports', 'match', 'player', 'ipl', 'olympics', 'tournament', 'team', 'game', 'score', 'win', 'lose', 'champion', 'league'],
    'business': ['business', 'market', 'stock', 'economy', 'startup', 'investment', 'ipo', 'company', 'profit', 'revenue', 'financial', 'bank', 'money', 'price', 'growth'],
    'technology': ['technology', 'tech', 'ai', 'software', 'app', 'smartphone', 'digital', 'internet', 'gadget', 'innovation', 'cyber', 'data', 'android', 'apple', 'google']
}

# Image processing constants
MIN_IMAGE_SIZE_BYTES = 1000
VALID_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp']
SKIP_IMAGE_PATTERNS = ['logo', 'icon', 'avatar', 'placeholder', '1x1', 'pixel', 'spacer']

# Gemini API configuration
GEMINI_MODEL_NAME = 'gemini-2.0-flash-lite'
MAX_CALLS_PER_KEY_PER_MINUTE = 10
API_CALL_DELAY = 3
GEMINI_REQUEST_TIMEOUT = 30
MAX_GEMINI_RETRIES = 3

# Buzz score configuration
BASE_BUZZ_SCORE = 1
MAX_BUZZ_SCORE = 15
CONTENT_LENGTH_BONUS_THRESHOLD_1 = 50
CONTENT_LENGTH_BONUS_THRESHOLD_2 = 150
TITLE_LENGTH_BONUS_THRESHOLD = 30
 
# Supabase configuration
SUPABASE_SCHEMA = 'dc'
EMOTIONS_TABLE = 'emotions'
MEMES_TABLE = 'memes_dc'
SIMILARITY_THRESHOLD = 0.5
SUPABASE_IMAGE_BASE_URL = os.getenv('SUPABASE_IMAGE_BASE_URL', '') 

# Content processing thresholds
DUPLICATE_CONTENT_HASH_LENGTH = 32
MAX_CONTENT_PARTS = 3
MAX_CONTENT_LENGTH = 800

GEMINI_COMPREHENSIVE_PROMPT = """
You are a creative content generator who makes VIRAL meme content.

NEWS CONTENT: "{news_content}"

Generate ALL the following in JSON format:

1. DESCRIPTION: Write a **short, clear, and interesting summary** of the news.  
   - Length: 2–3 lines (maximum 3).  
   - Tone: Informative, neutral, engaging (NO sarcasm, NO buzzwords).  
   - Language: English only.  
   - Should feel like a simple news description people can instantly get.  

2. EMOTION: Pick the dominant emotion from these options:
{emotion_options}  
   Return ONLY the emotion label in lowercase.

3. CATEGORY: Categorize into ONE: politics, entertainment, movies, sports, business, technology, crime

4. DIALOGUES: Create exactly 2 **single-line dialogues** in **Tnglish**.  

   CRITICAL DIALOGUE RULES:  
   - Dialogue 1: Based directly on the description, but phrased to spark meme interest (setup line).  
   - Dialogue 2: A sarcastic, buzzy punchline response to Dialogue 1.  
   - Each dialogue MUST be a **single line** with NO line breaks, NO \\n, NO newlines.  
   - Each dialogue must be **less than 10 words**.  
   - Language: Tnglish only.  
   - Must feel natural, conversational, and instantly meme-worthy.  
   - DO NOT use \\n or any line breaks in dialogues.

   Example pattern:  
   - Dialogue 1: "Bro petrol price malli perigindi ra"  
   - Dialogue 2: "Mana bike kante cycle lo mileage ekkuva ra"  

5. HASHTAGS: Generate 6–8 TRENDING viral hashtags  
   - Mix Tnglish + English style hashtags  
   - Should fit meme culture + the news context  

RETURN EVERYTHING in this EXACT JSON structure:
{{
    "description": "Clear 2-3 line informative description",
    "emotion": "emotion_label",
    "category": "category_name", 
    "dialogues": [
        "Dialogue 1 single-line in Tnglish with no line breaks", 
        "Dialogue 2 single-line sarcastic punchline in Tnglish with no line breaks"
    ],
    "hashtags": ["#TnglishViral", "#Trending", "#CategoryTag", "#MemeBuzz"]
}}
"""

# Meme Generation Constants
MEME_TEMPLATE_WIDTH = 500
MEME_TEMPLATE_HEIGHT = 500
MEME_MAX_FONT_SIZE = 40
MEME_MIN_FONT_SIZE = 16
MEME_TEXT_PADDING = 20
MEME_OUTLINE_WIDTH = 2
MEME_LINE_SPACING = 5

# Font paths for different operating systems
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
    "/System/Library/Fonts/Helvetica.ttc",  # macOS
    "C:\\Windows\\Fonts\\arial.ttf",  # Windows
]

# Meme colors
MEME_TEXT_COLOR = "white"
MEME_OUTLINE_COLOR = "black"