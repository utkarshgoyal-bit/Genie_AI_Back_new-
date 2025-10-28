from sqlalchemy import text
from app.config.db import engine
from typing import Optional

def get_all_products():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM products"))
            return [dict(row) for row in result.mappings()]
    except Exception as e:
        print("❌ ERROR in get_all_products:", e)
        raise

def get_products_by_disease(disease_name: str):
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM products WHERE disease ILIKE :disease"),
                {"disease": f"%{disease_name}%"}
            ).mappings().all()
            return [dict(row) for row in result]
    except Exception as e:
        print("❌ ERROR in get_products_by_disease:", e)
        raise

def get_products_by_scientific_name(
    disease_scientific_name: str, 
    plant_scientific_name: Optional[str] = None
):
    """
    Get products by disease scientific name, optionally filtered by plant.
    
    Args:
        disease_scientific_name: Scientific name of the disease (e.g., "Diplocarpon rosae")
        plant_scientific_name: Optional scientific name of the plant (e.g., "Rosa")
    """
    try:
        with engine.connect() as conn:
            # ✅ FIXED: Support both filtering modes
            if plant_scientific_name:
                # Filter by BOTH plant AND disease (more accurate)
                query = text("""
                    SELECT * FROM products
                    WHERE disease_scientific_name = :disease_scientific_name
                    AND scientific_name = :plant_scientific_name
                """)
                params = {
                    "disease_scientific_name": disease_scientific_name,
                    "plant_scientific_name": plant_scientific_name
                }
            else:
                # Filter by disease only (broader results)
                query = text("""
                    SELECT * FROM products
                    WHERE disease_scientific_name = :disease_scientific_name
                """)
                params = {"disease_scientific_name": disease_scientific_name}
            
            result = conn.execute(query, params).mappings().all()
            return [dict(row) for row in result]
            
    except Exception as e:
        print("❌ ERROR in get_products_by_scientific_name:", e)
        print(f"   Disease: {disease_scientific_name}, Plant: {plant_scientific_name}")
        raise