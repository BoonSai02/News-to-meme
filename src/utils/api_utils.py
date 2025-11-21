import time
import random
from typing import List, Dict
import sys
from src.logger import logging
from src.exceptions import CustomException

class APIKeyRotator:
    """Manages API key rotation and rate limiting"""
    
    def __init__(self, api_keys: List[str], max_calls_per_key_per_minute: int = 10):
        self.api_keys = [key for key in api_keys if key]
        if not self.api_keys:
            raise CustomException("No valid API keys provided", sys)
        
        self.max_calls_per_key_per_minute = max_calls_per_key_per_minute
        self.current_key_index = 0
        self.calls_per_key = {i: [] for i in range(len(self.api_keys))}
        
        logging.info(f"API Key Rotator initialized with {len(self.api_keys)} keys")

    def get_next_available_key_index(self) -> int:
        """Get next available API key index with proper rotation"""
        current_time = time.time()
        
        for attempt in range(len(self.api_keys)):
            key_index = (self.current_key_index + attempt) % len(self.api_keys)
            
            # Clean old timestamps for this key
            self.calls_per_key[key_index] = [
                t for t in self.calls_per_key[key_index] 
                if current_time - t < 60
            ]
            
            current_calls = len(self.calls_per_key[key_index])
            if current_calls < self.max_calls_per_key_per_minute:
                self.current_key_index = (key_index + 1) % len(self.api_keys)
                return key_index
        
        # If all keys are at limit, wait
        logging.info("All API keys at rate limit. Waiting 65 seconds...")
        time.sleep(65)
        
        # Clear all keys and reset
        for i in range(len(self.api_keys)):
            self.calls_per_key[i] = []
        self.current_key_index = 1
        return 0

    def record_api_call(self, key_index: int):
        """Record an API call for rate limiting"""
        current_time = time.time()
        self.calls_per_key[key_index].append(current_time)

    def get_api_key(self, key_index: int) -> str:
        """Get API key by index"""
        return self.api_keys[key_index]

def apply_rate_limiting(delay_seconds: int = 3):
    """Apply rate limiting delay between API calls"""
    time.sleep(delay_seconds + random.uniform(0.1, 0.5))
