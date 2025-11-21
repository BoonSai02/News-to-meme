import requests
import hashlib
from pathlib import Path
from urllib.parse import urljoin
from typing import Optional, List, Set
import sys
from src.logger import logging
from src.exceptions import CustomException

def is_valid_image_url(img_url: str, skip_patterns: List[str]) -> bool:
    """Check if image URL is valid for downloading"""
    if not img_url or len(img_url) < 10:
        return False
        
    img_lower = img_url.lower()
    
    if any(pattern in img_lower for pattern in skip_patterns):
        return False
    
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    return any(ext in img_url.lower() for ext in valid_extensions)

def normalize_image_url(img_url: str, base_url: str) -> Optional[str]:
    """Normalize image URL to absolute URL"""
    if not img_url or img_url.startswith('data:'):
        return None
    if img_url.startswith('//'):
        return 'https:' + img_url
    elif img_url.startswith('/'):
        return urljoin(base_url, img_url)
    elif img_url.startswith('http'):
        return img_url
    return urljoin(base_url + '/', img_url)

def get_image_url_from_element(img_element) -> Optional[str]:
    """Extract image URL from HTML element"""
    return (img_element.get('src') or 
            img_element.get('data-src') or 
            img_element.get('data-lazy-src'))

def download_image_with_validation(image_url: str, output_path: str, headers: dict, 
                                 min_size_bytes: int, downloaded_hashes: Set[str]) -> Optional[str]:
    """Download and validate image with deduplication"""
    try:
        response = requests.get(image_url, headers=headers, timeout=10)
        if response.status_code == 200:
            image_content = response.content
            if len(image_content) < min_size_bytes:
                return None
            
            image_hash = hashlib.sha256(image_content).hexdigest()
            if image_hash in downloaded_hashes:
                return None
            
            downloaded_hashes.add(image_hash)
            
            # Determine file extension
            ext = image_url.lower().split('.')[-1].split('?')[0]
            if ext not in ['jpg', 'jpeg', 'png', 'webp']:
                ext = 'jpg'
            
            # Create full path with extension
            final_path = f"{output_path}.{ext}"
            
            with open(final_path, 'wb') as f:
                f.write(image_content)
            
            return final_path
    except Exception as e:
        logging.warning(f"Failed to download image {image_url}: {str(e)}")
    return None

