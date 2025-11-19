import re
from rapidfuzz import process, fuzz
from functools import lru_cache
from typing import List, Tuple, Optional

def normalize(text: str) -> str:
    """
    Smarter text normalization that preserves more meaningful information:
    1. Converts to lowercase
    2. Standardizes spacing
    3. Keeps genus/species format
    4. Handles common variations
    """
    if not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower().strip()
    
    # Standardize spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Preserve scientific name format (Genus species)
    # but remove other special characters
    text = re.sub(r'[^a-z0-9\s\.]', '', text)
    
    # Handle common variations in scientific names
    text = text.replace('spp.', 'species')
    text = text.replace('var.', 'variety')
    text = text.replace('subsp.', 'subspecies')
    
    return text.strip()

def tokenize_scientific_name(name: str) -> List[str]:
    """
    Break scientific name into meaningful parts for better matching:
    - Genus
    - Species
    - Subspecies/Variety
    """
    tokens = normalize(name).split()
    return [t for t in tokens if t and t not in ('species', 'variety', 'subspecies')]

@lru_cache(maxsize=1024)
def fuzzy_lookup(query: str, choices: Tuple[str, ...], score_cutoff: int = 60) -> List[Tuple[str, int, int]]:
    """
    Enhanced fuzzy lookup that:
    1. Uses multiple scoring methods
    2. Considers partial matches
    3. Returns all matches above threshold
    4. Weights exact token matches higher
    """
    if not query or not choices:
        return []
    
    matches = []
    query_tokens = set(tokenize_scientific_name(query))
    
    for idx, choice in enumerate(choices):
        choice_tokens = set(tokenize_scientific_name(choice))
        
        # Calculate different types of matches
        token_ratio = len(query_tokens & choice_tokens) / max(len(query_tokens), len(choice_tokens))
        fuzzy_ratio = fuzz.WRatio(query, choice) / 100
        
        # Weight exact token matches higher
        combined_score = (token_ratio * 0.7 + fuzzy_ratio * 0.3) * 100
        
        if combined_score >= score_cutoff:
            matches.append((choice, int(combined_score), idx))
    
    # Sort by score descending
    return sorted(matches, key=lambda x: x[1], reverse=True)