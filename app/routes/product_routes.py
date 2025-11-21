from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from app.config.db import get_db
from app.controllers import product_controller_FINAL as product_controller
from typing import Optional

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/")
def get_products(db: Session = Depends(get_db)):
    """Get all products from database"""
    products = product_controller.get_all_products(db)
    if not products:
        raise HTTPException(status_code=404, detail="No products found")
    return products

@router.get("/by-scientific-name/{disease_scientific_name}")
def get_products_by_scientific_name(
    disease_scientific_name: str,
    plant_scientific_name: Optional[str] = Query(None)
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
def get_products_by_disease(disease_name: str, db: Session = Depends(get_db)):
    """Get products by disease name"""
    products = product_controller.get_products_by_disease(disease_name, db)
    if not products:
        raise HTTPException(status_code=404, detail="No products found for this disease")
    return products

@router.get("/search")
def search_products(
    disease_scientific_name: str = Query(...),
    plant_scientific_name: str = Query(...)
):
    """
    Search products by disease scientific name and plant scientific name.

    Query parameters:
    - disease_scientific_name: Scientific name of the disease (required)
    - plant_scientific_name: Scientific name of the plant (required)
    """
    products = product_controller.get_products_by_scientific_name(
        disease_scientific_name,
        plant_scientific_name
    )
    if not products:
        raise HTTPException(status_code=404, detail="No matching products found.")
    return products
