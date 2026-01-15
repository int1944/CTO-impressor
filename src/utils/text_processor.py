"""Text preprocessing and normalization utilities."""

import re
from typing import List


class TextProcessor:
    """Handles text normalization, tokenization, and preprocessing."""
    
    @staticmethod
    def normalize(text: str) -> str:
        """
        Normalize text for pattern matching.
        
        Args:
            text: Input text to normalize
            
        Returns:
            Normalized text (lowercase, trimmed, extra spaces removed)
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Trim
        text = text.strip()
        
        return text
    
    @staticmethod
    def tokenize(text: str) -> List[str]:
        """
        Tokenize text into words.
        
        Args:
            text: Input text to tokenize
            
        Returns:
            List of tokens (words)
        """
        if not text:
            return []
        
        # Normalize first
        normalized = TextProcessor.normalize(text)
        
        # Split on whitespace and punctuation
        tokens = re.findall(r'\b\w+\b', normalized)
        
        return tokens
    
    @staticmethod
    def get_last_n_words(text: str, n: int = 3) -> str:
        """
        Get the last N words from text.
        
        Args:
            text: Input text
            n: Number of words to extract
            
        Returns:
            Last N words as a string
        """
        tokens = TextProcessor.tokenize(text)
        if len(tokens) <= n:
            return text
        
        return ' '.join(tokens[-n:])
    
    @staticmethod
    def extract_context_window(text: str, cursor_position: int, window_size: int = 10) -> str:
        """
        Extract context around cursor position.
        
        Args:
            text: Full text
            cursor_position: Cursor position in text
            window_size: Number of characters before and after cursor
            
        Returns:
            Context window string
        """
        if not text:
            return ""
        
        start = max(0, cursor_position - window_size)
        end = min(len(text), cursor_position + window_size)
        
        return text[start:end]
