import os
import pandas as pd
import logging
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from app.models.product_model import Product
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductImportService:
    @staticmethod
    def import_products_from_excel(engine):
        excel_path = "Product_List.xlsx"
        if not os.path.exists(excel_path):
            logger.warning(f"Product_List.xlsx not found in current directory: {os.getcwd()}")
            # Try parent directory
            parent_excel_path = os.path.join(os.path.dirname(os.getcwd()), "Product_List.xlsx")
            if os.path.exists(parent_excel_path):
                excel_path = parent_excel_path
                logger.info(f"Found Product_List.xlsx in parent directory: {parent_excel_path}")
            else:
                logger.error("Product_List.xlsx not found in current or parent directory")
                return False

        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # Read and validate the Excel file
            df = pd.read_excel(excel_path)
            logger.info(f"Successfully read {len(df)} rows from {excel_path}")

            # Validate required columns
            required_cols = {'Scientific Plant Name', 'Disease', 'Scientific_Disease Name', 'Product Name', 'Product Link', 'How to use', 'Product Image'}
            if not required_cols.issubset(df.columns):
                logger.error(f"Excel file is missing required columns. Needed: {required_cols}. Found: {set(df.columns)}")
                return False

            # Clean and prepare data
            df = df.dropna(subset=['Scientific Plant Name', 'Scientific_Disease Name', 'Product Name'])  # Ensure essential fields aren't null
            
            with session.begin():
                # Clear existing products to ensure fresh data
                session.execute(text("DELETE FROM products"))
                logger.info("Cleared existing products from database")

                # Prepare products for insertion
                products_to_insert = []
                for idx, row in df.iterrows():
                    # Debug print the raw row data
                    logger.info(f"\nProcessing row {idx + 1}:")
                    for col in df.columns:
                        logger.info(f"{col}: {row[col]}")
                    
                    product = {
                        "product_name": str(row['Product Name']).strip() if pd.notna(row['Product Name']) else '',
                        "scientific_name": str(row['Scientific Plant Name']).strip() if pd.notna(row['Scientific Plant Name']) else '',
                        "disease": str(row['Disease']).strip() if pd.notna(row['Disease']) else '',
                        "disease_scientific_name": str(row['Scientific_Disease Name']).strip() if pd.notna(row['Scientific_Disease Name']) else '',
                        "product_link": str(row['Product Link']).strip() if pd.notna(row['Product Link']) else '',
                        "how_to_use": str(row['How to use']).strip() if pd.notna(row['How to use']) else '',
                    }
                    
                    # Debug print the processed product data
                    logger.info(f"Processed product data:")
                    for key, value in product.items():
                        logger.info(f"{key}: {value}")
                    
                    products_to_insert.append(product)
                    logger.info(f"Added product {len(products_to_insert)} to insert list\n")

                if products_to_insert:
                    logger.info(f"Inserting {len(products_to_insert)} products...")
                    try:
                        session.execute(
                            Product.__table__.insert(),
                            products_to_insert
                        )
                        session.commit()
                        logger.info(f"Successfully imported {len(products_to_insert)} products")
                        return True
                    except SQLAlchemyError as e:
                        logger.error(f"Database error during product import: {str(e)}")
                        session.rollback()
                        return False
                else:
                    logger.warning("No valid products found to import")
                    return False
                
        except Exception as e:
            logger.error(f"An error occurred during product import: {str(e)}", exc_info=True)
            if session:
                session.rollback()
            return False
        finally:
            if session:
                session.close()

    @staticmethod
    def get_product_stats(engine) -> Dict[str, Any]:
        try:
            with engine.connect() as conn:
                total = conn.execute(text("SELECT COUNT(id) FROM products")).scalar_one_or_none()
                unique_diseases = conn.execute(text("SELECT COUNT(DISTINCT disease_scientific_name) FROM products")).scalar_one_or_none()
                unique_plants = conn.execute(text("SELECT COUNT(DISTINCT scientific_name) FROM products")).scalar_one_or_none()
                return {"total_products": total or 0, "unique_diseases": unique_diseases or 0, "unique_plants": unique_plants or 0}
        except Exception as e:
            logger.error(f"Could not retrieve product stats: {e}", exc_info=True)
            return {}

    @staticmethod
    def get_product_stats(engine) -> Dict[str, Any]:
        try:
            with engine.connect() as conn:
                total = conn.execute(text("SELECT COUNT(id) FROM products")).scalar_one_or_none()
                unique_diseases = conn.execute(text("SELECT COUNT(DISTINCT disease_scientific_name) FROM products")).scalar_one_or_none()
                unique_plants = conn.execute(text("SELECT COUNT(DISTINCT scientific_name) FROM products")).scalar_one_or_none()
                return {"total_products": total or 0, "unique_diseases": unique_diseases or 0, "unique_plants": unique_plants or 0}
        except Exception as e:
            logger.error(f"Could not retrieve product stats: {e}", exc_info=True)
            return {}