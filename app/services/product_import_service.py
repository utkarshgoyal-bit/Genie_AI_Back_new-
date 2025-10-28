import pandas as pd
from sqlalchemy import text, inspect
from pathlib import Path

class ProductImportService:
    """Service to import products from Excel on startup"""
    
    @staticmethod
    def validate_database(engine) -> dict:
        """
        Combined validation: Check if table exists and has data.
        Returns: {"table_exists": bool, "has_data": bool}
        """
        try:
            inspector = inspect(engine)
            table_exists = 'products' in inspector.get_table_names()
            
            if not table_exists:
                return {"table_exists": False, "has_data": False}
            
            # Check if table has data
            with engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM products"))
                count = result.scalar()
                return {"table_exists": True, "has_data": count > 0}
                
        except Exception as e:
            print(f"⚠️ Error validating database: {e}")
            return {"table_exists": False, "has_data": False}
    
    @staticmethod
    def import_products_from_excel(engine, excel_path: str = "Product_List.xlsx"):
        """
        Import products from Excel file to database.
        Only runs if table is empty (prevents duplicates on restart).
        """
        try:
            # Check if file exists
            if not Path(excel_path).exists():
                print(f"⚠️ Product file not found: {excel_path}")
                print("📋 Skipping product import...")
                return False
            
            # Validate database
            validation = ProductImportService.validate_database(engine)
            
            if not validation["table_exists"]:
                print("⚠️ Products table doesn't exist. Run migrations first.")
                return False
            
            if validation["has_data"]:
                print("✅ Products already loaded in database. Skipping import.")
                return True
            
            # Read Excel file
            print(f"📂 Reading products from: {excel_path}")
            df = pd.read_excel(excel_path)
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Rename columns to match database schema
            df = df.rename(columns={
                "Plant Name": "scientific_name",
                "Disease": "disease",
                "Scientific Name": "disease_scientific_name",
                "Product Link": "product_link",
                "Product Name": "product_name",
                "How to use": "how_to_use",
                "Product Image": "product_image"
            })
            
            # Remove any existing data (safety check)
            with engine.connect() as conn:
                conn.execute(text("DELETE FROM products"))
                conn.commit()
            
            # Import to database
            df.to_sql("products", engine, if_exists="append", index=False)
            
            product_count = len(df)
            print(f"✅ Successfully imported {product_count} products to database!")
            return True
            
        except Exception as e:
            print(f"❌ Error importing products: {e}")
            return False
    
    @staticmethod
    def get_product_stats(engine) -> dict:
        """Get statistics about products in database"""
        try:
            with engine.connect() as conn:
                # Total products
                result = conn.execute(text("SELECT COUNT(*) FROM products"))
                total = result.scalar()
                
                # Unique diseases
                result = conn.execute(text("SELECT COUNT(DISTINCT disease) FROM products"))
                diseases = result.scalar()
                
                # Unique plants
                result = conn.execute(text("SELECT COUNT(DISTINCT scientific_name) FROM products"))
                plants = result.scalar()
                
                return {
                    "total_products": total,
                    "unique_diseases": diseases,
                    "unique_plants": plants
                }
        except Exception as e:
            print(f"⚠️ Error getting product stats: {e}")
            return {}