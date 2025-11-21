import hashlib
from difflib import SequenceMatcher
from typing import List, Dict
import sys
from src.logger import logging
from src.exceptions import CustomException

def clean_and_decide_content(title: str, extracted_content: str) -> str:
    """Clean content and decide between title/content to avoid duplicates"""
    clean_title = title.strip()
    clean_content = extracted_content.strip() if extracted_content else ""
    
    if not clean_content or len(clean_content) < 20:
        return clean_title
    
    title_normalized = ''.join(char.lower() for char in clean_title if char.isalnum() or char.isspace()).strip()
    content_normalized = ''.join(char.lower() for char in clean_content if char.isalnum() or char.isspace()).strip()
    
    if (content_normalized.startswith(title_normalized) or 
        title_normalized in content_normalized[:len(title_normalized) + 50]):
        return clean_content
    
    if len(clean_title) > len(clean_content):
        return clean_title
        
    return clean_content if len(clean_content) > len(clean_title) else clean_title

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate text similarity using sequence matcher"""
    return SequenceMatcher(None, text1.lower().strip(), text2.lower().strip()).ratio()

def find_most_similar_text(target: str, candidates: List[str], threshold: float = 0.5) -> str:
    """Find the most similar text from candidates"""
    if not candidates:
        return ""
    
    target_lower = target.lower().strip()
    
    # First try exact match
    for candidate in candidates:
        if candidate.lower().strip() == target_lower:
            return candidate
    
    # Then try similarity matching
    best_match = ""
    best_ratio = 0.0
    
    for candidate in candidates:
        similarity = calculate_similarity(target_lower, candidate)
        if similarity > best_ratio:
            best_ratio = similarity
            best_match = candidate
    
    if best_ratio > threshold:
        return best_match
    
    return candidates[0] if candidates else ""

def generate_content_hash(content: str) -> str:
    """Generate MD5 hash for content deduplication"""
    return hashlib.md5(content.encode()).hexdigest()

def remove_duplicates_by_content(articles: List[Dict]) -> List[Dict]:
    """Remove duplicate articles based on content hash"""
    unique_articles = []
    seen_hashes = set()
    
    for article in articles:
        content = article.get('content', '')
        content_hash = generate_content_hash(content)
        
        if content_hash not in seen_hashes:
            seen_hashes.add(content_hash)
            unique_articles.append(article)
    
    return unique_articles
