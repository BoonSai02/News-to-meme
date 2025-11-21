from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from PIL import Image
import numpy as np

@dataclass
class NewsExtractorArtifact:
    """Artifact returned by NewsExtractor component"""
    scraped_articles: List[Dict[str, Any]]
    total_articles: int
    sources_scraped: List[str]
    
@dataclass
class ContentProcessorArtifact:
    """Artifact returned by ContentProcessor component"""
    processed_articles: List[Dict[str, Any]]
    categorized_news: Dict[str, List[Dict[str, Any]]]
    unique_articles_count: int
    
@dataclass
class ImageDownloaderArtifact:
    """Artifact returned by ImageDownloader component"""
    downloaded_images: List[str]
    failed_downloads: List[str]
    total_images_processed: int
    images_directory: str
    
@dataclass
class GeminiProcessorArtifact:
    """Artifact returned by GeminiProcessor component"""
    processed_content: List[Dict[str, Any]]
    total_api_calls: int
    success_rate: float
    failed_articles: List[str]
    
@dataclass
class TemplateManagerArtifact:
    """Artifact returned by TemplateManager component"""
    matched_templates: List[str]
    template_success_rate: float
    emotions_matched: List[str]
    unmatched_emotions: List[str]
    
@dataclass
class OutputManagerArtifact:
    """Artifact returned by OutputManager component"""
    output_file_path: str
    total_articles_saved: int
    file_size_bytes: int
    timestamp: str
    
@dataclass
class MemeGeneratorArtifact:
    generated_memes_count: int
    failed_memes_count: int
    total_processing_time: float
    success_rate: float
    average_generation_time: float

