import pandas as pd
import re
from sqlalchemy import text, inspect
from pathlib import Path

class ProductImportService:
    """Service to import products from Excel on startup"""
    
    # Mapping of common plant names to scientific names
    PLANT_NAME_MAPPING = {
        "Rose": "Rosa",
        "Tomato": "Solanum lycopersicum",
        "Curry Leaf": "Murraya koenigii",
        "Peace Lily": "Spathiphyllum spp.",
        "Hibiscus": "Hibiscus rosa-sinensis",
        "Croton": "Codiaeum variegatum",
        "Fiddle Leaf Fig": "Ficus lyrata",
        "Snake Plant": "Dracaena trifasciata",
        "Pothos": "Epipremnum aureum",
        "Areca Palm": "Dypsis lutescens",
    }
    
    @staticmethod
    def clean_scientific_name(name):
        """
        Remove extra text from scientific names.
        Example: "Alternaria solani (fungus)" → "Alternaria solani"
        """
        if not name or pd.isna(name):
            return name
        
        # Convert to string
        name = str(name)
        
        # Remove text in parentheses
        cleaned = re.sub(r'\s*\([^)]*\)', '', name)
        
        # Remove extra whitespace
        cleaned = ' '.join(cleaned.split())
        
        return cleaned.strip()
    
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
            
            # Clean column names (remove extra spaces)
            df.columns = df.columns.str.strip()
            
            print(f"📊 Found columns: {list(df.columns)}")
            
            # Check which column structure we have
            has_scientific_plant = 'Scientific Plant Name' in df.columns
            has_common_plant = 'Plant Name' in df.columns
            has_scientific_disease_underscore = 'Scientific_Disease Name' in df.columns
            has_scientific_disease_space = 'Scientific Disease Name' in df.columns
            has_scientific_name = 'Scientific Name' in df.columns
            
            # Handle plant name column
            if has_scientific_plant:
                print("✅ Found 'Scientific Plant Name' column")
                df['scientific_name'] = df['Scientific Plant Name']
            elif has_common_plant:
                print("🔄 Found 'Plant Name' column, mapping to scientific names...")
                df['scientific_name'] = df['Plant Name'].map(
                    ProductImportService.PLANT_NAME_MAPPING
                )
                # Use common name as fallback for unmapped plants
                df['scientific_name'] = df['scientific_name'].fillna(df['Plant Name'])
                
                unmapped = df[df['Plant Name'].notna() & 
                            ~df['Plant Name'].isin(ProductImportService.PLANT_NAME_MAPPING.keys())]['Plant Name'].unique()
                if len(unmapped) > 0:
                    print(f"⚠️ Warning: {len(unmapped)} unmapped plant names (using as-is):")
                    for plant in unmapped[:5]:
                        print(f"   - {plant}")
            else:
                print("⚠️ Warning: No plant name column found")
                df['scientific_name'] = None
            
            # Handle disease scientific name column
            disease_col = None
            if has_scientific_disease_underscore:
                disease_col = 'Scientific_Disease Name'
                print(f"✅ Found '{disease_col}' column")
            elif has_scientific_disease_space:
                disease_col = 'Scientific Disease Name'
                print(f"✅ Found '{disease_col}' column")
            elif has_scientific_name:
                disease_col = 'Scientific Name'
                print(f"✅ Found '{disease_col}' column (using as disease scientific name)")
            
            if disease_col:
                print("🧹 Cleaning disease scientific names...")
                df['disease_scientific_name'] = df[disease_col].apply(
                    ProductImportService.clean_scientific_name
                )
            else:
                print("⚠️ Warning: No disease scientific name column found")
                df['disease_scientific_name'] = None
            
            # Handle common disease name
            if 'Disease' in df.columns:
                df['disease'] = df['Disease']
            else:
                print("⚠️ Warning: No 'Disease' column found")
                df['disease'] = None
            
            # Handle other columns with flexible naming
            if 'Product Link' in df.columns:
                df['product_link'] = df['Product Link']
            elif 'product_link' in df.columns:
                df['product_link'] = df['product_link']
            
            if 'Product Name' in df.columns:
                df['product_name'] = df['Product Name']
            elif 'product_name' in df.columns:
                df['product_name'] = df['product_name']
            
            if 'How to use' in df.columns:
                df['how_to_use'] = df['How to use']
            elif 'how_to_use' in df.columns:
                df['how_to_use'] = df['how_to_use']
            
            if 'Product Image' in df.columns:
                df['product_image'] = df['Product Image']
            elif 'product_image' in df.columns:
                df['product_image'] = df['product_image']
            
            # Select only the columns we need for the database
            final_columns = ['scientific_name', 'disease', 'disease_scientific_name', 
                           'product_link', 'product_name', 'how_to_use', 'product_image']
            
            df_final = df[final_columns]
            
            # Verify we have the essential columns
            essential = ['disease', 'product_name']
            missing_essential = [col for col in essential if df_final[col].isna().all()]
            if missing_essential:
                print(f"❌ Essential columns are empty: {missing_essential}")
                return False
            
            # Remove any existing data (safety check)
            with engine.connect() as conn:
                conn.execute(text("DELETE FROM products"))
                conn.commit()
            
            # Import to database
            df_final.to_sql("products", engine, if_exists="append", index=False)
            
            product_count = len(df_final)
            print(f"✅ Successfully imported {product_count} products to database!")
            
            # Show sample data for verification
            print("\n📋 Sample imported data:")
            sample = df_final.head(3)
            for idx, row in sample.iterrows():
                print(f"   Plant: {row['scientific_name']} | Disease: {row['disease_scientific_name']} | Product: {row['product_name']}")
            
            # Show statistics
            print(f"\n📊 Import Statistics:")
            print(f"   Unique plants: {df_final['scientific_name'].nunique()}")
            print(f"   Unique diseases (common): {df_final['disease'].nunique()}")
            print(f"   Unique diseases (scientific): {df_final['disease_scientific_name'].nunique()}")
            print(f"   Products with scientific plant names: {df_final['scientific_name'].notna().sum()}")
            print(f"   Products with scientific disease names: {df_final['disease_scientific_name'].notna().sum()}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error importing products: {e}")
            import traceback
            traceback.print_exc()
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