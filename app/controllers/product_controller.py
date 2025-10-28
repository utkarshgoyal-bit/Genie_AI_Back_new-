from sqlalchemy import text
from app.config.db import engine

def get_all_products():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM products"))
            return [dict(row) for row in result.mappings()]
    except Exception as e:
        print(":x: ERROR in get_all_products:", e)
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
        print(":x: ERROR in get_products_by_disease:", e)
        raise
        
def get_products_by_scientific_name(disease_scientific_name: str, scientific_name: str):
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT * FROM products
                    WHERE disease_scientific_name = :disease_scientific_name
                    AND scientific_name = :scientific_name
                """),
                {
                    "disease_scientific_name": disease_scientific_name,
                    "scientific_name": scientific_name
                }
            ).mappings().all()
            return [dict(row) for row in result]
    except Exception as e:
        print(":x: ERROR in get_products_by_scientific_name:", e)
        raise





















