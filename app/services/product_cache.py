import logging
from sqlalchemy import text
from app.config.db import engine
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

PRODUCT_CACHE: List[Dict[str, Any]] = []

def load_products_into_cache():
    """
    Loads all products from the database into an in-memory list.
    """
    global PRODUCT_CACHE
    logger.info("Initializing product cache...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM products")).mappings().all()
            PRODUCT_CACHE = [dict(row) for row in result]
            logger.info(f"Successfully loaded {len(PRODUCT_CACHE)} products into in-memory cache.")
    except Exception as e:
        logger.critical(f"Failed to load products into cache. Search will not work. Error: {e}", exc_info=True)
        PRODUCT_CACHE = []

def get_cached_products() -> List[Dict[str, Any]]:
    """Returns the cached list of products."""
    return PRODUCT_CACHE