import re
from rapidfuzz import process, fuzz
from functools import lru_cache
from typing import List, Tuple, Optional

def normalize(text: str) -> str:
    """
    Normalizes text by converting to lowercase and removing special characters.
    """
    if not isinstance(text, str):
        return ""
    return re.sub(r'[^a-z0-9\s]', '', text.lower()).strip()

@lru_cache(maxsize=1024)
def fuzzy_lookup(query: str, choices: Tuple[str, ...], score_cutoff: int = 80) -> Optional[Tuple[str, int, int]]:
    """
    Performs a fuzzy lookup for a query against a tuple of choices.
    Uses lru_cache to cache results for repeated lookups.
    """
    if not query or not choices:
        return None
    
    result = process.extractOne(query, choices, scorer=fuzz.WRatio, score_cutoff=score_cutoff)
    
    if result:
        best_match, score, index = result
        return best_match, int(score), index
    return None