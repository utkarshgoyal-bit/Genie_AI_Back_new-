from fastapi import APIRouter, HTTPException
from app.controllers import product_controller

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/")
def get_products():
    products = product_controller.get_all_products()
    if not products:
        raise HTTPException(status_code=404, detail="No products found")
    return products

@router.get("/by-scientific-name/{disease_scientific_name}")
def get_products_by_scientific_name(disease_scientific_name: str, scientific_name: str):
    products = product_controller.get_products_by_scientific_name(disease_scientific_name, scientific_name)
    if not products:
        raise HTTPException(status_code=404, detail="No products found for this plant and scientific name")
    return products

@router.get("/by-disease/{disease_name}")
def get_products_by_disease(disease_name: str):
    products = product_controller.get_products_by_disease(disease_name)
    if not products:
        raise HTTPException(status_code=404, detail="No products found for this disease")
    return products






