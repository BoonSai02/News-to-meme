import base64
import io
import time
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Tuple
import os
import sys
from src.entity.config_entity import MemeGeneratorConfig, ConfigEntity
from src.entity.artifacts import MemeGeneratorArtifact
from src.logger import logging
from src.exceptions import CustomException


class MemeGenerator:
    def __init__(self):
        self.config = MemeGeneratorConfig(config=ConfigEntity())
        self.font_path = self._get_available_font()
        self.generated_count = 0
        self.failed_count = 0
        self.total_time = 0.0
        
        logging.info("MemeGenerator initialized with configuration")

    def _get_available_font(self):
        """Get the first available font from the system"""
        for font_path in self.config.font_paths:
            if os.path.exists(font_path):
                logging.info(f"Using font: {font_path}")
                return font_path
        
        logging.warning("No system fonts found, using default font")
        return None

    def calculate_font_size(self, text: str, max_width: int, max_height: int) -> int:
        """Calculate optimal font size based on text length and available space"""
        text_length = len(text)
        
        # Base font size calculation on text length
        if text_length <= 15:
            base_size = self.config.max_font_size
        elif text_length <= 30:
            base_size = self.config.max_font_size - 6
        elif text_length <= 50:
            base_size = self.config.max_font_size - 12
        else:
            base_size = self.config.max_font_size - 18
        
        # Ensure font size is within bounds
        font_size = max(min(base_size, self.config.max_font_size), self.config.min_font_size)
        
        return font_size

    def draw_text_with_outline(self, draw, position, text, font, fill_color=None, outline_color=None, outline_width=None):
        """Draw text with black outline for better visibility"""
        if fill_color is None:
            fill_color = self.config.text_color
        if outline_color is None:
            outline_color = self.config.outline_color
        if outline_width is None:
            outline_width = self.config.outline_width
            
        x, y = position
        
        # Draw outline
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
        
        # Draw main text
        draw.text(position, text, font=font, fill=fill_color)

    def wrap_text(self, text: str, font, max_width: int) -> List[str]:
        """Wrap text to fit within specified width"""
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            
            try:
                if hasattr(font, 'getbbox'):
                    bbox = font.getbbox(test_line)
                    text_width = bbox[2] - bbox[0]
                elif hasattr(font, 'getsize'):
                    size = font.getsize(test_line)
                    text_width = size[0]
                else:
                    # Fallback: estimate width
                    text_width = len(test_line) * (font.size // 2)
            except:
                text_width = len(test_line) * 8
            
            if text_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                    current_line = word
                else:
                    lines.append(word)  # Word is too long, add anyway
        
        if current_line:
            lines.append(current_line)
        
        return lines

    def generate_meme_with_overlay(self, template_url_or_bytes, dialogues: List[str]) -> str:
        """Overlay dialogues on template and return base64"""
        start_time = time.time()
    
        try:
            if not template_url_or_bytes or not dialogues:
                logging.warning("Missing template data or dialogues")
                self.failed_count += 1
                return ""
        
        # Load template image
            try:
                if isinstance(template_url_or_bytes, bytes):
                # If bytes are provided directly
                    template_image = Image.open(io.BytesIO(template_url_or_bytes))
                    logging.debug("Template loaded from bytes")
                else:
                # If it's a URL or path, download it
                    from src.utils.supabase_utils import download_template_from_url
                    from src.entity.config_entity import TemplateManagerConfig, ConfigEntity
                
                    config = TemplateManagerConfig(config=ConfigEntity())
                    template_bytes = download_template_from_url(config.supabase_image_base_url, template_url_or_bytes)
                
                    if not template_bytes:
                        logging.error("Failed to download template")
                        self.failed_count += 1
                        return ""
                
                    template_image = Image.open(io.BytesIO(template_bytes))
                    logging.debug("Template downloaded and loaded successfully")
                
            except Exception as e:
                logging.error(f"Error loading template: {str(e)}")
                self.failed_count += 1
                return ""
        
            # Convert to RGB if needed
            if template_image.mode != 'RGB':
                template_image = template_image.convert('RGB')
        
            # Resize template to standard size
            template_image = template_image.resize(
                (self.config.template_width, self.config.template_height), 
                Image.Resampling.LANCZOS
            )
        
            # Create drawing context
            draw = ImageDraw.Draw(template_image)
        
            # Get font
            try:
                if self.font_path and isinstance(self.font_path, str):
                    default_font = ImageFont.truetype(self.font_path, self.config.max_font_size)
                else:
                    default_font = ImageFont.load_default()
            except:
                default_font = ImageFont.load_default()
        
        # Process dialogues (top and bottom)
            if len(dialogues) >= 1 and dialogues[0].strip():
            # Top text
                top_text = dialogues[0].strip().upper()
                top_font_size = self.calculate_font_size(
                    top_text, 
                    self.config.template_width - 2 * self.config.text_padding, 
                    100
                )
            
                try:
                    if self.font_path and isinstance(self.font_path, str):
                        top_font = ImageFont.truetype(self.font_path, top_font_size)
                    else:
                        top_font = ImageFont.load_default()
                except:
                    top_font = ImageFont.load_default()
            
            # Wrap text
                max_text_width = self.config.template_width - 2 * self.config.text_padding
                top_lines = self.wrap_text(top_text, top_font, max_text_width)
            
            # Position top text
                y_offset = self.config.text_padding
                for line in top_lines:
                    try:
                        if hasattr(top_font, 'getbbox'):
                            bbox = top_font.getbbox(line)
                            text_width = bbox[2] - bbox[0]
                        elif hasattr(top_font, 'getsize'):
                            size = top_font.getsize(line)
                            text_width = size[0]
                        else:
                            text_width = len(line) * (top_font_size // 2)
                    except:
                        text_width = len(line) * (top_font_size // 2)
                
                    x_position = (self.config.template_width - text_width) // 2
                    x_position = max(
                        self.config.text_padding, 
                        min(x_position, self.config.template_width - text_width - self.config.text_padding)
                    )
                
                    self.draw_text_with_outline(draw, (x_position, y_offset), line, top_font)
                    y_offset += top_font_size + self.config.line_spacing
        
            if len(dialogues) >= 2 and dialogues[1].strip():
            # Bottom text
                bottom_text = dialogues[1].strip().upper()
                bottom_font_size = self.calculate_font_size(
                    bottom_text, 
                    self.config.template_width - 2 * self.config.text_padding, 
                    100
            )
            
                try:
                    if self.font_path and isinstance(self.font_path, str):
                        bottom_font = ImageFont.truetype(self.font_path, bottom_font_size)
                    else:
                        bottom_font = ImageFont.load_default()
                except:
                    bottom_font = ImageFont.load_default()
            
            # Wrap text
                max_text_width = self.config.template_width - 2 * self.config.text_padding
                bottom_lines = self.wrap_text(bottom_text, bottom_font, max_text_width)
            
            # Calculate starting y position (from bottom)
                total_text_height = len(bottom_lines) * (bottom_font_size + self.config.line_spacing) - self.config.line_spacing
                y_offset = self.config.template_height - total_text_height - self.config.text_padding
            
                for line in bottom_lines:
                    try:
                        if hasattr(bottom_font, 'getbbox'):
                            bbox = bottom_font.getbbox(line)
                            text_width = bbox[2] - bbox[0]
                        elif hasattr(bottom_font, 'getsize'):
                            size = bottom_font.getsize(line)
                            text_width = size[0]
                        else:
                            text_width = len(line) * (bottom_font_size // 2)
                    except:
                        text_width = len(line) * (bottom_font_size // 2)
                
                    x_position = (self.config.template_width - text_width) // 2
                    x_position = max(
                        self.config.text_padding, 
                        min(x_position, self.config.template_width - text_width - self.config.text_padding)
                    )
                
                    self.draw_text_with_outline(draw, (x_position, y_offset), line, bottom_font)
                    y_offset += bottom_font_size + self.config.line_spacing
        
        # Convert back to base64
            output_buffer = io.BytesIO()
            template_image.save(output_buffer, format='PNG', quality=95)
            output_base64 = base64.b64encode(output_buffer.getvalue()).decode('utf-8')
        
        # Update statistics
            processing_time = time.time() - start_time
            self.total_time += processing_time
            self.generated_count += 1
        
            logging.info(f"Meme generated successfully with {len(dialogues)} dialogues in {processing_time:.2f}s")
            return output_base64
        
        except Exception as e:
            processing_time = time.time() - start_time
            self.total_time += processing_time
            self.failed_count += 1
         
            logging.error(f"Error generating meme: {str(e)}")
            raise CustomException(e, sys)

    def get_generation_statistics(self) -> MemeGeneratorArtifact:
        """Get generation statistics"""
        return MemeGeneratorArtifact(
            generated_memes_count=self.generated_count,
            failed_memes_count=self.failed_count,
            total_processing_time=self.total_time,
            success_rate=0.0,  # Will be calculated in __post_init__
            average_generation_time=0.0  # Will be calculated in __post_init__
        )

    def reset_statistics(self):
        """Reset generation statistics"""
        self.generated_count = 0
        self.failed_count = 0
        self.total_time = 0.0
        logging.info("MemeGenerator statistics reset")
