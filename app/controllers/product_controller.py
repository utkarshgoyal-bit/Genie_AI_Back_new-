import os
import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.config.db import get_db
from app.models.product_model import Product
from app.services.match_utils import fuzzy_lookup, normalize
from app.services.product_cache import get_cached_products
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCORE_CUTOFF = int(os.getenv("FUZZY_SCORE_CUTOFF", 85))
WEIGHT_DISEASE = float(os.getenv("FUZZY_WEIGHT_DISEASE", 0.6))
WEIGHT_PLANT = float(os.getenv("FUZZY_WEIGHT_PLANT", 0.4))

router = APIRouter()

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