from fastapi import APIRouter, HTTPException, Query, Depends
from app.controllers import product_controller as product_controller
from app.config.db import get_db
from sqlalchemy.orm import Session
from typing import Optional

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/")
def get_products(db: Session = Depends(get_db)):
    products = product_controller.get_all_products(db)
    if not products:
        raise HTTPException(status_code=404, detail="No products found")
    return products

@router.get("/by-scientific-name/{disease_scientific_name}")
def get_products_by_scientific_name(
    disease_scientific_name: str,
    plant_scientific_name: Optional[str] = Query(None)  # ✅ FIXED: Made optional with Query
):
    """
    Get products by disease scientific name, optionally filtered by plant.
    
    Examples:
    - /products/by-scientific-name/Diplocarpon%20rosae
    - /products/by-scientific-name/Diplocarpon%20rosae?plant_scientific_name=Rosa
    """
    products = product_controller.get_products_by_scientific_name(
        disease_scientific_name, 
        plant_scientific_name
    )
    if not products:
        raise HTTPException(
            status_code=404, 
            detail="No products found for this disease" + 
                   (f" and plant {plant_scientific_name}" if plant_scientific_name else "")
        )
    return products

@router.get("/by-disease/{disease_name}")
def get_products_by_disease(disease_name: str):
    products = product_controller.get_products_by_disease(disease_name)
    if not products:
        raise HTTPException(status_code=404, detail="No products found for this disease")
    return products