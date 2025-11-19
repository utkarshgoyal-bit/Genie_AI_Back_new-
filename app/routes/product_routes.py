import logging
from fastapi import APIRouter, HTTPException, Query
from app.controllers import product_controller
from app.services.match_utils import normalize, fuzzy_lookup
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Products"])

@router.get("/products", response_model=List[Dict[str, Any]])
async def get_products():
    """Get all products from the cache"""
    try:
        products = product_controller.get_all_products()
        if not products:
            raise HTTPException(status_code=404, detail="No products found")
        return products
    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/products/search", response_model=List[Dict[str, Any]])
async def search_products(
    disease_scientific_name: str = Query(..., description="Scientific name of the disease"),
    plant_scientific_name: str = Query(..., description="Scientific name of the plant")
):
    """
    Search for products based on disease and plant scientific names.
    Uses smart matching including exact, token-based and fuzzy matching.
    """
    try:
        # Get all products first
        all_products = product_controller.get_all_products()
        if not all_products:
            raise HTTPException(status_code=404, detail="No products found in database")

        # Normalize search terms
        norm_disease = normalize(disease_scientific_name)
        norm_plant = normalize(plant_scientific_name)

        logger.info(f"Searching for disease: {norm_disease}, plant: {norm_plant}")

        matched_products = []
        for product in all_products:
            if not product.get('disease_scientific_name') or not product.get('scientific_name'):
                continue

            # Normalize product terms
            product_disease = normalize(product['disease_scientific_name'])
            product_plant = normalize(product['scientific_name'])

            # Calculate match scores
            disease_score = fuzzy_lookup(norm_disease, (product_disease,), score_cutoff=60)
            plant_score = fuzzy_lookup(norm_plant, (product_plant,), score_cutoff=60)

            if disease_score and plant_score:
                disease_match = disease_score[0][1]
                plant_match = plant_score[0][1]
                
                # Combined weighted score
                total_score = (disease_match * 0.6) + (plant_match * 0.4)
                
                if total_score >= 60:  # Lower threshold for better matching
                    matched_products.append({
                        "product": product,
                        "score": total_score,
                        "match_details": {
                            "disease_match": disease_match,
                            "plant_match": plant_match
                        }
                    })

        # Sort by score and take top matches
        matched_products.sort(key=lambda x: x['score'], reverse=True)
        top_matches = matched_products[:5]  # Get top 5 matches

        if not top_matches:
            raise HTTPException(status_code=404, detail="No matching products found")

        # Return the matched products with their scores
        return [match['product'] for match in top_matches]

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in product search: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error searching for products: {str(e)}"
        )

@router.get("/by-disease/{disease_name}")
def get_products_by_disease(disease_name: str):
    products = product_controller.get_products_by_disease(disease_name)
    if not products:
        raise HTTPException(status_code=404, detail="No products found for this disease")
    return products