from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.domains.analyze import router as analyze_router
from app.domains.products import router as product_router, load_products_into_cache
from app.domains.auth import router as auth_router
from app.domains.history import router as history_router
from app.utils import Base, engine
from app.models import Product
from app.services.product_import_service import ProductImportService
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "="*60)
    print("🚀 STARTING APPLICATION")
    print("="*60)
    
    print("📊 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables ready")
    
    print("\n📦 Checking product database...")
    ProductImportService.import_products_from_excel(engine)
    
    print("\n💾 Loading products into in-memory cache...")
    load_products_into_cache()
    
    stats = ProductImportService.get_product_stats(engine)
    if stats:
        print(f"\n📊 PRODUCT DATABASE STATS:")
        print(f"  Total Products: {stats.get('total_products', 0)}")
        print(f"  Unique Diseases: {stats.get('unique_diseases', 0)}")
        print(f"  Unique Plants: {stats.get('unique_plants', 0)}")
    
    print("\n✅ APPLICATION READY!")
    print("="*60 + "\n")
    
    yield
    
    print("\n👋 Shutting down application...")


app = FastAPI(title="Plant Disease Detection API", version="4.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(analyze_router)
app.include_router(product_router)
app.include_router(auth_router)
app.include_router(history_router)


@app.get("/")
def root():
    return {
        "status": "Plant Disease Detection API v4.2.0",
        "message": "API is running successfully"
    }


@app.get("/health")
def health_check():
    stats = ProductImportService.get_product_stats(engine)
    return {
        "status": "healthy",
        "database": "connected",
        "products_loaded": stats.get('total_products', 0) > 0,
        "product_stats": stats
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
