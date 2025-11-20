import os
import pandas as pd
import logging
import csv
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from app.models.product_model import Product
from app.services.match_utils import fuzzy_lookup, normalize
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCORE_CUTOFF = int(os.getenv("FUZZY_SCORE_CUTOFF", 85))
UNMAPPED_LOG_FILE = "unmapped_plants_log.csv"

class ProductImportService:
    @staticmethod
    def _log_unmapped_plant(data):
        file_exists = os.path.isfile(UNMAPPED_LOG_FILE)
        with open(UNMAPPED_LOG_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)

    @staticmethod
    def import_products_from_excel(engine):
        excel_path = "Product_List.xlsx"
        if not os.path.exists(excel_path):
            logger.warning(f"'{excel_path}' not found. Skipping product import.")
            return

        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            with session.begin():
                count_result = session.execute(text("SELECT COUNT(*) FROM products")).scalar()
                if count_result > 0:
                    logger.info("Product table is not empty. Skipping import.")
                    return

                df = pd.read_excel(excel_path)
                required_cols = {'product_name', 'scientific_name', 'disease_common_name', 'disease_scientific_name'}
                if not required_cols.issubset(df.columns):
                    logger.error(f"Excel file is missing required columns. Needed: {required_cols}. Found: {set(df.columns)}")
                    raise ValueError("Invalid Excel schema")

                plant_map_df = pd.read_excel("Plant_Map.xlsx")
                plant_map = dict(zip(plant_map_df['Common Name'], plant_map_df['Scientific Name']))
                normalized_map = {normalize(k): v for k, v in plant_map.items()}
                map_choices = tuple(normalized_map.keys())

                products_to_insert = []
                for _, row in df.iterrows():
                    common_name = row.get('plant_common_name')
                    scientific_name = row.get('scientific_name')

                    if pd.isna(scientific_name) and pd.notna(common_name):
                        norm_common = normalize(common_name)
                        match_result = fuzzy_lookup(norm_common, map_choices, score_cutoff=SCORE_CUTOFF)
                        
                        if match_result:
                            matched_norm_name, score, _ = match_result
                            scientific_name = normalized_map[matched_norm_name]
                            if score < 95:
                                ProductImportService._log_unmapped_plant({"product_name": row.get('product_name'), "input_common_name": common_name, "matched_scientific_name": scientific_name, "score": score, "status": "low_confidence_match"})
                        else:
                            ProductImportService._log_unmapped_plant({"product_name": row.get('product_name'), "input_common_name": common_name, "matched_scientific_name": "N/A", "score": 0, "status": "unmapped"})
                            continue

                    if pd.notna(scientific_name):
                        products_to_insert.append({"product_name": row.get('product_name'), "scientific_name": scientific_name, "disease_common_name": row.get('disease_common_name'), "disease_scientific_name": row.get('disease_scientific_name')})

                if products_to_insert:
                    logger.info(f"Bulk inserting {len(products_to_insert)} products...")
                    session.execute(Product.__table__.insert(), products_to_insert)
                
                logger.info("Product import process completed successfully.")
        except Exception as e:
            logger.error(f"An error occurred during product import. Rolling back transaction. Error: {e}", exc_info=True)
            session.rollback()
            raise
        finally:
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