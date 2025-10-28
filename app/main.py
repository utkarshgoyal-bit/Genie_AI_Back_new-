import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routes.analyze_routes import router as analyze_router
from app.routes.product_routes import router as product_router
from app.routes.otp_routes import router as otp_routes
from app.routes.history_routes import router as history_router
from app.config.db import Base, engine
from app.models.product_model import Product
from app.services.product_import_service import ProductImportService
from app.services.product_cache import load_products_into_cache
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "="*60)
    print("🚀 STARTING APPLICATION")
    print("="*60)
    
    print("📊 Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables ready")
    except Exception as db_error:
        print(f"❌ Error creating database tables: {str(db_error)}")
        raise
    
    print("\n📦 Checking product database...")
    try:
        excel_path = "Product_List.xlsx"
        parent_excel_path = os.path.join(os.path.dirname(os.getcwd()), "Product_List.xlsx")
        
        if os.path.exists(excel_path):
            print(f"✅ Found Product_List.xlsx in current directory")
        elif os.path.exists(parent_excel_path):
            print(f"✅ Found Product_List.xlsx in parent directory")
            excel_path = parent_excel_path
        else:
            print("❌ Product_List.xlsx not found!")
            print("   Please ensure Product_List.xlsx is present in the root directory")
            print(f"   Current directory: {os.getcwd()}")
            print(f"   Parent directory: {os.path.dirname(os.getcwd())}")
            raise FileNotFoundError("Product_List.xlsx not found")

        if ProductImportService.import_products_from_excel(engine):
            print("✅ Product import successful")
            
            # Reload cache immediately after successful import
            print("\n💾 Loading products into in-memory cache...")
            load_products_into_cache()
            print("✅ Products loaded into cache")
        else:
            print("❌ Product import failed. Check logs for details.")
            raise Exception("Product import failed")
            
    except Exception as error:
        print(f"❌ Error during product setup: {str(error)}")
        raise
    
    stats = ProductImportService.get_product_stats(engine)
    if stats:
        print(f"\n📊 PRODUCT DATABASE STATS:")
        print(f"   Total Products: {stats.get('total_products', 0)}")
        print(f"   Unique Diseases: {stats.get('unique_diseases', 0)}")
        print(f"   Unique Plants: {stats.get('unique_plants', 0)}")
    
    print("\n✅ APPLICATION READY!")
    print("="*60 + "\n")
    
    yield
    
    print("\n👋 Shutting down application...")

app = FastAPI(title="Plant Disease Detection API", version="4.2.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(analyze_router)
app.include_router(product_router)
app.include_router(otp_routes)
app.include_router(history_router)

@app.get("/")
def root():
    return {"status": "Plant Disease Detection API v4.2.0", "message": "API is running successfully"}

@app.get("/health")
def health_check():
    stats = ProductImportService.get_product_stats(engine)
    return {"status": "healthy", "database": "connected", "products_loaded": stats.get('total_products', 0) > 0, "product_stats": stats}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)