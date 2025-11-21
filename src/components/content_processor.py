import sys
from typing import List, Dict
from src.entity.artifacts import ContentProcessorArtifact
from src.entity.config_entity import ContentProcessorConfig, ConfigEntity
from src.logger import logging
from src.exceptions import CustomException
from src.utils.text_utils import remove_duplicates_by_content

class ContentProcessor:
    def __init__(self):
        self.config = ContentProcessorConfig(config=ConfigEntity())
        logging.info("ContentProcessor initialized")

    def calculate_buzz_score(self, title: str, content: str) -> int:
        """Calculate buzz score for article prioritization"""
        try:
            text = (title + ' ' + content).lower()
            buzz_score = self.config.base_buzz_score
            
            # Add points for high buzz keywords
            for keyword, points in self.config.high_buzz_words.items():
                if keyword in text:
                    buzz_score += points
            
            # Add points for category keywords
            for keyword, points in self.config.category_buzz_words.items():
                if keyword in text:
                    buzz_score += points
            
            # Content quality bonus
            if len(content) > self.config.content_length_bonus_threshold_1:
                buzz_score += 1
            if len(content) > self.config.content_length_bonus_threshold_2:
                buzz_score += 1
            
            # Title engagement bonus
            if any(word in title.lower() for word in ['how', 'why', 'what', 'when', 'where']):
                buzz_score += 1
            
            # Length bonus for substantial content
            if len(title) > self.config.title_length_bonus_threshold:
                buzz_score += 1
            
            return min(buzz_score, self.config.max_buzz_score)
            
        except Exception as e:
            logging.error(f"Error calculating buzz score: {str(e)}")
            return self.config.base_buzz_score

    def categorize_content(self, title: str, content: str, source_category: str = None) -> str:
        """Categorize news content based on keywords"""
        try:
            text = (title + ' ' + content).lower()
            
            # If source has predefined category, use it first
            if source_category and source_category in self.config.target_categories:
                return source_category
            
            # Score each category
            category_scores = {}
            for category, keywords in self.config.category_keywords.items():
                score = sum(1 if keyword in text else 0 for keyword in keywords)
                category_scores[category] = score
            
            # Return category with highest score
            if category_scores:
                best_category = max(category_scores, key=category_scores.get)
                if category_scores[best_category] > 0:
                    return best_category
            
            # Default fallback
            return source_category if source_category in self.config.target_categories else 'entertainment'
            
        except Exception as e:
            logging.error(f"Error categorizing content: {str(e)}")
            return 'entertainment'

    def process_articles(self, articles: List[Dict]) -> ContentProcessorArtifact:
        """Process articles with buzz scoring and categorization"""
        try:
            # Remove duplicates first
            unique_articles = remove_duplicates_by_content(articles)
            logging.info(f"Removed duplicates: {len(articles)} -> {len(unique_articles)} articles")
            
            # Process each article
            processed_articles = []
            for article in unique_articles:
                # Calculate buzz score
                buzz_score = self.calculate_buzz_score(article['title'], article['content'])
                
                # Categorize content
                category = self.categorize_content(
                    article['title'], 
                    article['content'], 
                    article.get('category')
                )
                
                # Only keep articles from target categories
                if category not in self.config.target_categories:
                    continue
                
                # Add processed metadata
                processed_article = article.copy()
                processed_article.update({
                    'buzz_score': buzz_score,
                    'final_category': category
                })
                
                processed_articles.append(processed_article)
            
            # Organize by categories
            categorized_news = {}
            for category in self.config.target_categories:
                categorized_news[category] = []
            
            # Group by category
            for article in processed_articles:
                category = article.get('final_category', 'entertainment')
                if category in categorized_news:
                    categorized_news[category].append(article)
            
            # Select top articles per category
            final_categorized = {}
            for category in self.config.target_categories:
                category_articles = categorized_news[category]
                
                if len(category_articles) >= self.config.articles_per_category:
                    # Sort by buzz score and take top articles
                    category_articles.sort(key=lambda x: x.get('buzz_score', 0), reverse=True)
                    selected_articles = category_articles[:self.config.articles_per_category]
                else:
                    # Take all available
                    selected_articles = category_articles
                    logging.warning(f"Only {len(selected_articles)} articles found for {category}")
                    
                    # Fill remaining slots from entertainment if possible
                    if category != 'entertainment' and len(selected_articles) < self.config.articles_per_category:
                        entertainment_extras = [a for a in categorized_news.get('entertainment', []) 
                                              if a not in selected_articles][:self.config.articles_per_category - len(selected_articles)]
                        selected_articles.extend(entertainment_extras)
                        logging.info(f"Added {len(entertainment_extras)} entertainment articles to fill {category}")
                
                final_categorized[category] = selected_articles
                logging.info(f"{category.upper()}: {len(selected_articles)} articles selected")
            
            total_selected = sum(len(articles) for articles in final_categorized.values())
            logging.info(f"Content processing completed: {total_selected} articles selected")
            
            return ContentProcessorArtifact(
                processed_articles=processed_articles,
                categorized_news=final_categorized,
                unique_articles_count=len(unique_articles)
            )
            
        except Exception as e:
            logging.error(f"Error in process_articles: {str(e)}")
            raise CustomException(e, sys)
