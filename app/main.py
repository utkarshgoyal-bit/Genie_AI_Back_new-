from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routes.analyze_routes import router as analyze_router
from app.routes.product_routes import router as product_router
from app.routes.otp_routes import router as otp_routes  
from app.routes.history_routes import router as history_router     
from app.config.db import Base, engine   
from app.models.detection_model import PlantDetection
from app.models.product_model import Product  # ← ADD THIS LINE
from app.services.product_import_service import ProductImportService
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events.
    Runs once when application starts/stops.
    """
    # STARTUP
    print("\n" + "="*60)
    print("🚀 STARTING APPLICATION")
    print("="*60)
    
    # Create database tables (including products table)
    print("📊 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables ready")
    
    # Import products from Excel
    print("\n📦 Checking product database...")
    ProductImportService.import_products_from_excel(engine)
    
    # Get product stats
    stats = ProductImportService.get_product_stats(engine)
    if stats:
        print(f"\n📊 PRODUCT DATABASE STATS:")
        print(f"   Total Products: {stats.get('total_products', 0)}")
        print(f"   Unique Diseases: {stats.get('unique_diseases', 0)}")
        print(f"   Unique Plants: {stats.get('unique_plants', 0)}")
    
    print("\n✅ APPLICATION READY!")
    print("="*60 + "\n")
    
    yield  # Application runs here
    
    # SHUTDOWN
    print("\n👋 Shutting down application...")


# Create FastAPI app with lifespan
app = FastAPI(
    title="Plant Disease Detection API", 
    version="4.2.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(analyze_router)
app.include_router(product_router)
app.include_router(otp_routes)
app.include_router(history_router)

@app.get("/")
def root():
    return {
        "status": "Plant Disease Detection API v4.2.0",
        "message": "API is running successfully"
    }

@app.get("/health")
def health_check():
    """Health check endpoint for deployment monitoring"""
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