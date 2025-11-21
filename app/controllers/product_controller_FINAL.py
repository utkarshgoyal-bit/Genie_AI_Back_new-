import os
import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.config.db import get_db
from app.models.product_model import Product
from app.services.match_utils import fuzzy_lookup, normalize
from app.services.product_cache import get_cached_products
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCORE_CUTOFF = int(os.getenv("FUZZY_SCORE_CUTOFF", 85))
WEIGHT_DISEASE = float(os.getenv("FUZZY_WEIGHT_DISEASE", 0.6))
WEIGHT_PLANT = float(os.getenv("FUZZY_WEIGHT_PLANT", 0.4))

router = APIRouter()


# ============================================================================
# NEW FUNCTIONS FOR DIAGNOSIS-BASED PRODUCT MATCHING
# ============================================================================

def calculate_similarity(str1: str, str2: str) -> float:
    """
    Calculate similarity ratio between two strings using SequenceMatcher (0.0 to 1.0)

    Args:
        str1: First string to compare
        str2: Second string to compare

    Returns:
        Similarity ratio (0.0 = no match, 1.0 = perfect match)
    """
    if not str1 or not str2:
        return 0.0

    # Normalize: lowercase and strip whitespace
    s1 = str1.lower().strip()
    s2 = str2.lower().strip()

    return SequenceMatcher(None, s1, s2).ratio()


def find_product_by_diagnosis(
    plant_scientific_name: str,
    plant_common_name: str,
    disease_name: str,
    db: Session,
    threshold: float = 0.70
) -> Optional[Dict[str, Any]]:
    """
    FUZZY MATCHING: Find product recommendation based on AI diagnosis

    Strategy:
    1. Try matching plant_scientific_name + disease against Product_List
    2. If no match above threshold, fallback to plant_common_name + disease
    3. Return best match above threshold with confidence score

    Args:
        plant_scientific_name: Scientific name from AI (e.g., "Rosa")
        plant_common_name: Common name from AI (e.g., "Rose")
        disease_name: Disease/issue from AI (e.g., "Black Spot", "Nitrogen Deficiency")
        db: Database session
        threshold: Minimum similarity score (default 0.70 = 70%)

    Returns:
        Dict with product details + match_confidence, or None if no match
    """

    logger.info(f"🔍 Fuzzy matching: Plant='{plant_scientific_name}'/'{plant_common_name}', Disease='{disease_name}'")

    # Get all products from database
    all_products = db.query(Product).all()

    if not all_products:
        logger.warning("No products in database")
        return None

    best_match = None
    best_score = 0.0
    best_match_type = None

    # PHASE 1: Try matching with scientific name first
    logger.info(f"  → Phase 1: Trying scientific name '{plant_scientific_name}'")

    for product in all_products:
        # Calculate plant similarity (scientific name)
        plant_similarity = calculate_similarity(
            plant_scientific_name,
            product.scientific_name or ""
        )

        # Calculate disease similarity
        disease_similarity = calculate_similarity(
            disease_name,
            product.disease or ""
        )

        # Combined score (weighted average: 50% plant, 50% disease)
        combined_score = (plant_similarity * 0.5) + (disease_similarity * 0.5)

        if combined_score > best_score:
            best_score = combined_score
            best_match = product
            best_match_type = "scientific_name"
            logger.debug(f"    New best: {product.product_name} (score: {combined_score:.2%})")

    # PHASE 2: If no good match with scientific name, try common name fallback
    if best_score < threshold and plant_common_name:
        logger.info(f"  → Phase 2: Fallback to common name '{plant_common_name}' (Phase 1 score: {best_score:.2%})")

        for product in all_products:
            # Calculate plant similarity (common name vs scientific name in DB)
            # Note: Product_List.xlsx only has "Scientific Plant Name" column
            # So we fuzzy match common name against scientific names in database
            plant_similarity = calculate_similarity(
                plant_common_name,
                product.scientific_name or ""
            )

            # Calculate disease similarity
            disease_similarity = calculate_similarity(
                disease_name,
                product.disease or ""
            )

            # Combined score
            combined_score = (plant_similarity * 0.5) + (disease_similarity * 0.5)

            if combined_score > best_score:
                best_score = combined_score
                best_match = product
                best_match_type = "common_name_fallback"
                logger.debug(f"    New best: {product.product_name} (score: {combined_score:.2%})")

    # Check if best match meets threshold
    if best_score >= threshold and best_match:
        logger.info(f"✅ Match found: {best_match.product_name} (score: {best_score:.2%}, type: {best_match_type})")

        return {
            "product_id": best_match.id,
            "product_name": best_match.product_name,
            "disease": best_match.disease,
            "scientific_name": best_match.scientific_name,
            "match_confidence": round(best_score, 4),
            "match_type": best_match_type
        }
    else:
        logger.info(f"❌ No match above threshold {threshold:.0%} (best score: {best_score:.2%})")
        return None


# ============================================================================
# EXISTING API ROUTES (UNCHANGED)
# ============================================================================

@router.get("/products", response_model=List[Dict[str, Any]])
def get_all_products(db: Session = Depends(get_db)):
    try:
        products = db.query(Product).all()
        return [p.to_dict() for p in products]
    except Exception as e:
        logger.error(f"Error fetching all products: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error.")


@router.get("/products/search", response_model=List[Dict[str, Any]])
def get_products_by_scientific_name(disease_scientific_name: str, plant_scientific_name: str):
    if not disease_scientific_name and not plant_scientific_name:
        raise HTTPException(status_code=400, detail="Please provide at least one search parameter.")

    all_products = get_cached_products()

    if not all_products:
        logger.warning("Product cache is empty. Search service is unavailable.")
        raise HTTPException(status_code=503, detail="Product service is temporarily unavailable.")

    norm_disease = normalize(disease_scientific_name)
    norm_plant = normalize(plant_scientific_name)

    scored_products = []
    for product in all_products:
        disease_score = 0
        plant_score = 0

        if norm_disease and product.get("disease_scientific_name"):
            match = fuzzy_lookup(norm_disease, (normalize(product["disease_scientific_name"]),), score_cutoff=0)
            if match:
                disease_score = match[1]

        if norm_plant and product.get("scientific_name"):
            match = fuzzy_lookup(norm_plant, (normalize(product["scientific_name"]),), score_cutoff=0)
            if match:
                plant_score = match[1]

        combined_score = (disease_score * WEIGHT_DISEASE) + (plant_score * WEIGHT_PLANT)

        if combined_score >= SCORE_CUTOFF:
            scored_products.append({"product": product, "score": round(combined_score, 2)})

    top_results = sorted(scored_products, key=lambda x: x["score"], reverse=True)[:3]

    logger.info("Fuzzy search performed", extra={"search_terms": {"disease": norm_disease, "plant": norm_plant}, "results_count": len(top_results)})

    if not top_results:
        raise HTTPException(status_code=404, detail="No matching products found.")

    return [result["product"] for result in top_results]


@router.get("/products/by-disease/{disease_name}", response_model=List[Dict[str, Any]])
def get_products_by_disease(disease_name: str, db: Session = Depends(get_db)):
    try:
        safe_disease_name = disease_name.replace('%', '\\%').replace('_', '\\_')
        products = db.query(Product).filter(Product.disease_common_name.ilike(f"%{safe_disease_name}%")).all()
        return [p.to_dict() for p in products]
    except Exception as e:
        logger.error(f"Error fetching products by disease '{disease_name}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error.")
