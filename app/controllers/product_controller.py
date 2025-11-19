import os
import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.config.db import get_db
from app.models.product_model import Product
from app.services.match_utils import fuzzy_lookup, normalize, tokenize_scientific_name
from app.services.product_cache import get_cached_products
from typing import List, Dict, Any
from difflib import SequenceMatcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCORE_CUTOFF = int(os.getenv("FUZZY_SCORE_CUTOFF", 85))
WEIGHT_DISEASE = float(os.getenv("FUZZY_WEIGHT_DISEASE", 0.6))
WEIGHT_PLANT = float(os.getenv("FUZZY_WEIGHT_PLANT", 0.4))

def fuzzy_match_score(a: str, b: str) -> float:
    """Calculate a fuzzy match score between two strings."""
    if not a or not b:
        return 0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() * 100

router = APIRouter()

@router.get("/products", response_model=List[Dict[str, Any]])
def get_all_products():
    try:
        logger.info("Fetching products from cache")
        return get_cached_products()
    except Exception as e:
        logger.error(f"Error fetching products from cache: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching products: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error fetching all products: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching products: {str(e)}"
        )

@router.get("/products/search", response_model=List[Dict[str, Any]])
async def get_products_by_scientific_name(disease_scientific_name: str, plant_scientific_name: str):
    """
    Enhanced product search that uses a tiered matching approach:
    1. Try exact scientific name matches first
    2. Then try token-based matching
    3. Finally fall back to fuzzy matching
    """
    logger.info(f"Starting product search with disease: {disease_scientific_name}, plant: {plant_scientific_name}")
    
    try:
        if not disease_scientific_name and not plant_scientific_name:
            raise HTTPException(status_code=400, detail="Please provide at least one search parameter.")

        all_products = get_cached_products()
        if not all_products:
            logger.warning("Product cache is empty. Search service is unavailable.")
            raise HTTPException(status_code=503, detail="Product service is temporarily unavailable.")

        logger.info(f"Searching products for disease '{disease_scientific_name}' and plant '{plant_scientific_name}'")
        logger.info(f"Total products in cache: {len(all_products)}")

        # Normalize input
        norm_disease = normalize(disease_scientific_name)
        norm_plant = normalize(plant_scientific_name)
        
        # Track matches at different confidence levels
        exact_matches = []
        strong_matches = []
        fuzzy_matches = []

        logger.info(f"Normalized search terms - Disease: {norm_disease}, Plant: {norm_plant}")

        for product in all_products:
            product_disease = normalize(product.get("disease_scientific_name", ""))
            product_plant = normalize(product.get("scientific_name", ""))
            
            # Try exact matches first (case-insensitive)
            logger.info(f"\nChecking product:")
            logger.info(f"Product Name: {product.get('product_name')}")
            logger.info(f"Scientific Name: {product.get('scientific_name')}")
            logger.info(f"Disease: {product.get('disease')}")
            logger.info(f"Disease Scientific Name: {product.get('disease_scientific_name')}")
            
            # First try exact match
            if norm_disease == product_disease and norm_plant == product_plant:
                logger.info(f"✅ EXACT MATCH - Score: 100")
                exact_matches.append({
                    "product": product,
                    "score": 100,
                    "match_type": "exact"
                })
                continue

            # Try fuzzy matching for disease and plant separately
            disease_score = fuzzy_match_score(norm_disease, product_disease)
            plant_score = fuzzy_match_score(norm_plant, product_plant)

            # Calculate weighted score
            combined_score = (disease_score * WEIGHT_DISEASE + plant_score * WEIGHT_PLANT)
            
            logger.info(f"Matching scores:")
            logger.info(f"Disease match: {disease_score:.2f}% ({norm_disease} vs {product_disease})")
            logger.info(f"Plant match: {plant_score:.2f}% ({norm_plant} vs {product_plant})")
            logger.info(f"Combined score: {combined_score:.2f}%")

            if combined_score >= 85:  # Strong match
                logger.info(f"Found strong match: {product.get('product_name')} (Score: {combined_score:.2f})")
                strong_matches.append({"product": product, "score": combined_score})
            elif combined_score >= 70:  # Fuzzy match
                logger.info(f"Found fuzzy match: {product.get('product_name')} (Score: {combined_score:.2f})")
                fuzzy_matches.append({"product": product, "score": combined_score})
            
            # Fall back to fuzzy matching for remaining cases
            disease_matches = fuzzy_lookup(norm_disease, (product_disease,), score_cutoff=60)
            plant_matches = fuzzy_lookup(norm_plant, (product_plant,), score_cutoff=60)
            
            if disease_matches and plant_matches:
                disease_score = disease_matches[0][1]
                plant_score = plant_matches[0][1]
                fuzzy_score = (disease_score * 0.6 + plant_score * 0.4)
                if fuzzy_score >= 60:  # 60% fuzzy match threshold
                    fuzzy_matches.append({"product": product, "score": fuzzy_score})

        # Combine results in priority order
        all_matches = exact_matches + strong_matches + fuzzy_matches
        
        # Sort by score and take top matches
        top_results = sorted(all_matches, key=lambda x: x["score"], reverse=True)[:5]

        logger.info(f"Search results - Exact: {len(exact_matches)}, Strong: {len(strong_matches)}, Fuzzy: {len(fuzzy_matches)}")

        if not top_results:
            logger.warning(f"No products found matching disease '{disease_scientific_name}' and plant '{plant_scientific_name}'")
            raise HTTPException(status_code=404, detail="No matching products found.")

        # Return full product details
        matched_products = []
        logger.info("\nFinal matches:")
        for match in top_results:
            product = match["product"]
            product_details = {
                "id": len(matched_products) + 1,
                "product_name": product.get("name", "N/A"),  # Changed from product_name to name
                "product_link": product.get("product_link", "N/A"),
                "how_to_use": product.get("how_to_use", "N/A"),
                "match_score": round(match["score"], 2),
                "disease": product.get("disease", "N/A"),
                "disease_scientific_name": product.get("disease_scientific_name", "N/A"),
                "plant_scientific_name": product.get("scientific_name", "N/A")
            }
            logger.info(f"\nMatch {product_details['id']}:")
            for key, value in product_details.items():
                logger.info(f"{key}: {value}")
            matched_products.append(product_details)

        return matched_products
    except Exception as e:
        logger.error(f"Error searching for products: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error searching for products: {str(e)}"
        )

@router.get("/products/by-disease/{disease_name}", response_model=List[Dict[str, Any]])
def get_products_by_disease(disease_name: str, db: Session = Depends(get_db)):
    try:
        safe_disease_name = disease_name.replace('%', '\\%').replace('_', '\\_')
        products = db.query(Product).filter(Product.disease_common_name.ilike(f"%{safe_disease_name}%")).all()
        return [p.to_dict() for p in products]
    except Exception as e:
        logger.error(f"Error fetching products by disease '{disease_name}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error.")