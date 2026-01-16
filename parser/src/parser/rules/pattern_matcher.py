"""Pattern matching utilities for rules."""

import re
from typing import List, Optional, Tuple


class PatternMatcher:
    """Utilities for pattern matching and regex operations."""
    
    @staticmethod
    def match_pattern(text: str, pattern: str, case_sensitive: bool = False) -> Optional[re.Match]:
        """
        Match a regex pattern against text.
        
        Args:
            text: Text to search in
            pattern: Regex pattern
            case_sensitive: Whether matching should be case sensitive
            
        Returns:
            Match object if found, None otherwise
        """
        flags = 0 if case_sensitive else re.IGNORECASE
        return re.search(pattern, text, flags)
    
    @staticmethod
    def match_any_pattern(text: str, patterns: List[str], case_sensitive: bool = False) -> Optional[Tuple[re.Match, str]]:
        """
        Match text against any of the provided patterns.
        
        Args:
            text: Text to search in
            patterns: List of regex patterns
            case_sensitive: Whether matching should be case sensitive
            
        Returns:
            Tuple of (match object, matched pattern) if found, None otherwise
        """
        for pattern in patterns:
            match = PatternMatcher.match_pattern(text, pattern, case_sensitive)
            if match:
                return (match, pattern)
        return None
    
    @staticmethod
    def extract_groups(text: str, pattern: str, case_sensitive: bool = False) -> List[str]:
        """
        Extract all groups from a pattern match.
        
        Args:
            text: Text to search in
            pattern: Regex pattern with groups
            case_sensitive: Whether matching should be case sensitive
            
        Returns:
            List of matched groups
        """
        match = PatternMatcher.match_pattern(text, pattern, case_sensitive)
        if match:
            return list(match.groups())
        return []
    
    @staticmethod
    def has_word_boundary(text: str, word: str) -> bool:
        """
        Check if text contains word with proper word boundaries.
        
        Args:
            text: Text to search in
            word: Word to find
            
        Returns:
            True if word found with boundaries
        """
        pattern = r'\b' + re.escape(word) + r'\b'
        return PatternMatcher.match_pattern(text, pattern) is not None
