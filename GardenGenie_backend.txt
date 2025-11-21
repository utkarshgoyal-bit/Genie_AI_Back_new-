# Garden Genie AI Backend - Codebase Context Document

**Generated**: November 19, 2025  
**Version**: 4.2.0  
**Branch**: improvement1  
**Status**: Active Development

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Directory Structure](#directory-structure)
5. [Key Components](#key-components)
6. [Database Schema](#database-schema)
7. [API Endpoints](#api-endpoints)
8. [Configuration](#configuration)
9. [Recent Changes & Improvements](#recent-changes--improvements)
10. [Development Setup](#development-setup)
11. [Deployment](#deployment)
12. [Known Issues & Limitations](#known-issues--limitations)
13. [Future Roadmap](#future-roadmap)

---

## Project Overview

**Garden Genie AI** is a plant disease detection and product recommendation system that uses AI and computer vision to help users identify plant diseases and recommend suitable products for treatment.

### Key Features

- 🌱 **Plant Disease Detection**: Uses YOLO v8 model for plant species identification
- 🤖 **AI-Powered Analysis**: OpenAI GPT-4 for detailed disease analysis and recommendations
- 📊 **Product Database**: 181+ products covering 10+ plant species
- 🔍 **Smart Search**: Fuzzy matching for flexible product discovery
- 📱 **Mobile Integration**: Connected APK for mobile user interface
- ⚡ **Performance**: In-memory caching for lightning-fast product searches
- 🔐 **Security**: JWT authentication, CORS support
- 📝 **Logging**: Comprehensive logging for debugging and monitoring

### Current Statistics

- **Total Products**: 181
- **Unique Diseases**: 76
- **Plant Species**: 10
- **API Version**: 4.2.0

---

## Architecture

The application follows a **modular, layered architecture**:

```
┌─────────────────────────────────────────┐
│         FastAPI Application             │
│        (app.main:app)                   │
├─────────────────────────────────────────┤
│                                          │
│  ┌──────────────────────────────────┐   │
│  │      Route Layer (Routes)        │   │
│  │ ├─ analyze_routes.py            │   │
│  │ ├─ product_routes.py            │   │
│  │ ├─ history_routes.py            │   │
│  │ └─ otp_routes.py                │   │
│  └──────────────────────────────────┘   │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │   Controller Layer (Controllers) │   │
│  │ └─ product_controller.py         │   │
│  └──────────────────────────────────┘   │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │    Service Layer (Services)      │   │
│  │ ├─ product_import_service.py    │   │
│  │ ├─ product_cache.py             │   │
│  │ ├─ match_utils.py               │   │
│  │ ├─ analyze_service.py           │   │
│  │ ├─ image_utils.py               │   │
│  │ └─ analyze_service_v4.py        │   │
│  └──────────────────────────────────┘   │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │    Data Layer (Models & DB)      │   │
│  │ ├─ product_model.py             │   │
│  │ ├─ detection_model.py           │   │
│  │ ├─ otp_model.py                 │   │
│  │ └─ config/db.py                 │   │
│  └──────────────────────────────────┘   │
│                                          │
└─────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────┐
│  PostgreSQL Database     │
│  (Neon Cloud)           │
└──────────────────────────┘
         │
         ▼
┌──────────────────────────┐
│  YOLO v8 Model          │
│  (best.pt)              │
└──────────────────────────┘
         │
         ▼
┌──────────────────────────┐
│  OpenAI API (GPT-4)      │
└──────────────────────────┘
```

---

## Technology Stack

### Core Framework
- **FastAPI** (0.115.5) - Modern, fast web framework
- **Uvicorn** (0.32.1) - ASGI server

### Database & ORM
- **PostgreSQL** (15+) - Primary database
- **SQLAlchemy** (2.0.36) - ORM for database operations
- **Psycopg2** (2.9.10) - PostgreSQL adapter
- **Alembic** (1.14.0) - Database migrations

### Computer Vision & AI
- **Ultralytics** (8.3.209) - YOLO v8 model
- **OpenCV Headless** (4.10.0.84) - Image processing
- **Pillow** (11.0.0) - Image handling
- **OpenAI** (1.57.2) - GPT-4 integration

### Data Processing
- **Pandas** (2.2.2) - Data manipulation
- **OpenPyXL** (3.1.2) - Excel file handling
- **RapidFuzz** (3.14.1) - Fuzzy string matching

### Security & Authentication
- **PyJWT** (2.10.1) - JWT tokens
- **Python-Jose** (3.3.0) - JSON Web Signature (JWS)
- **Passlib** (1.7.4) - Password hashing
- **Cryptography** (46.0.3) - Encryption

### Cloud & Storage
- **Boto3** (1.35.71) - AWS SDK
- **AWS S3** - Image storage (configured)

### Utilities
- **Python-dotenv** (1.0.1) - Environment variables
- **Pydantic** (2.10.3) - Data validation
- **Pydantic-Settings** (2.6.1) - Settings management
- **Requests** (2.32.3) - HTTP client
- **HTTPX** (0.28.1) - Async HTTP client

### Development & Deployment
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Python** (3.11-slim) - Runtime

---

## Directory Structure

```
Genie_AI_Backend/
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI application entry point
│   ├── config/
│   │   ├── __init__.py
│   │   └── db.py                        # Database configuration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── product_model.py             # Product ORM model
│   │   ├── detection_model.py           # Detection history model
│   │   ├── otp_model.py                 # OTP model
│   │   └── best.pt                      # YOLO v8 model weights
│   ├── controllers/
│   │   ├── __init__.py
│   │   └── product_controller.py        # Product search logic
│   ├── services/
│   │   ├── __init__.py
│   │   ├── product_import_service.py    # Excel import & data loading
│   │   ├── product_cache.py             # In-memory product cache
│   │   ├── match_utils.py               # Fuzzy matching utilities
│   │   ├── analyze_service.py           # Plant disease analysis (v1)
│   │   ├── analyze_service_v2.py        # Plant disease analysis (v2)
│   │   ├── analyze_service_v4.py        # Plant disease analysis (v4) - Current
│   │   └── image_utils.py               # Image processing utilities
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── analyze_routes.py            # Image analysis endpoints
│   │   ├── product_routes.py            # Product search endpoints
│   │   ├── history_routes.py            # Detection history endpoints
│   │   └── otp_routes.py                # OTP verification endpoints
│   └── utils/
│       ├── __init__.py
│       └── [utility modules]
│
├── uploads/                              # Uploaded image storage (gitignored)
│   └── [image files]
│
├── docker-compose.yml                   # Docker Compose configuration
├── Dockerfile                           # Docker image definition
├── requirements.txt                     # Python dependencies
├── .env                                 # Environment variables (SENSITIVE)
├── .env.example                         # Example env template
├── .gitignore                           # Git ignore rules
├── .dockerignore                        # Docker ignore rules
├── README.md                            # Project readme
├── Product_List.xlsx                    # Product database (Excel)
├── Plant_Map.xlsx                       # Plant mapping file (Excel)
└── CODEBASE_CONTEXT.md                  # This file
```

---

## Key Components

### 1. Application Entry Point (`app/main.py`)

**Responsibility**: Initialize FastAPI application with all routes and middleware

**Key Features**:
- **Lifespan Context Manager**: Handles startup and shutdown events
  - Creates database tables on startup
  - Imports products from Excel file
  - Loads all products into in-memory cache
  - Displays product statistics
- **CORS Middleware**: Allows cross-origin requests from any domain
- **Route Registration**: Includes all route modules
- **Health Check Endpoint**: `/health` returns API status and database stats

**Critical Flow**:
1. Application starts
2. Database tables are created (if not exist)
3. Product import service checks if products exist
4. If empty, imports from `Product_List.xlsx`
5. Loads all products into memory for fast searching
6. API becomes ready to accept requests

### 2. Database Configuration (`app/config/db.py`)

**Responsibility**: Database connection and session management

**Key Exports**:
- `engine`: SQLAlchemy engine for database operations
- `Base`: Declarative base for ORM models
- `get_db()`: Dependency injection function for database sessions

**Environment Variables Used**:
- `DATABASE_URL`: PostgreSQL connection string (from Neon Cloud)

### 3. Product Model (`app/models/product_model.py`)

**Responsibility**: ORM mapping for products table

**Fields**:
- `id`: Primary key
- `product_name`: Name of the product
- `scientific_name`: Scientific name of plant species
- `disease_common_name`: Common name of disease
- `disease_scientific_name`: Scientific name of disease
- `[other fields]`: Additional product details

### 4. Product Controller (`app/controllers/product_controller.py`)

**Responsibility**: Core business logic for product search

**Key Methods**:

1. **`get_all_products()`**
   - Returns all products from database
   - Used for general product listing

2. **`get_products_by_scientific_name()`**
   - **Most Important Function** for search
   - Uses fuzzy matching for flexible searches
   - Combines disease and plant name matching
   - Returns top 3 results sorted by relevance
   - **Weighted Scoring**:
     - Disease match: 60% weight
     - Plant match: 40% weight
   - **Configurable via .env**:
     - `FUZZY_SCORE_CUTOFF`: Minimum combined score (default: 85)
     - `FUZZY_WEIGHT_DISEASE`: Disease weight (default: 0.6)
     - `FUZZY_WEIGHT_PLANT`: Plant weight (default: 0.4)

3. **`get_products_by_disease()`**
   - Filters products by disease name
   - Uses SQL ILIKE for case-insensitive matching
   - Includes SQL injection protection

### 5. Product Cache Service (`app/services/product_cache.py`)

**Responsibility**: In-memory product storage for performance

**Key Functions**:
- `load_products_into_cache()`: Loads all products from DB to memory on startup
- `get_cached_products()`: Returns cached products

**Performance Impact**:
- First load: ~100-500ms (depends on product count)
- Subsequent searches: <10ms (memory access)
- Significant performance improvement vs. database queries

### 6. Match Utilities (`app/services/match_utils.py`)

**Responsibility**: Fuzzy string matching for product search

**Key Functions**:

1. **`normalize(text: str) -> str`**
   - Converts text to lowercase
   - Removes special characters
   - Normalizes whitespace
   - Example: `"Leaf-Spot (Fungal)"` → `"leafspot fungal"`

2. **`fuzzy_lookup(query, choices, score_cutoff)`**
   - Uses RapidFuzz library with WRatio scorer
   - LRU caching (1024 results) for repeated lookups
   - Returns: `(best_match, score, index)`
   - Score: 0-100 (100 = exact match)

**Usage Example**:
```python
fuzzy_lookup(
    "powdery mildew",
    ("powdery mildew", "downy mildew", "leaf spot"),
    score_cutoff=80
)
# Returns: ("powdery mildew", 100, 0)
```

### 7. Product Import Service (`app/services/product_import_service.py`)

**Responsibility**: Excel import and data management

**Key Methods**:

1. **`import_products_from_excel(engine)`**
   - Reads `Product_List.xlsx`
   - Checks if products already exist (skips if yes)
   - Uses fuzzy matching to map common plant names to scientific names
   - Logs unmapped plants to `unmapped_plants_log.csv`
   - Bulk inserts products into database
   - **Transaction Management**: Uses SQLAlchemy session.begin() for ACID compliance

2. **`get_product_stats(engine)`**
   - Returns total products, unique diseases, unique plants
   - Used for health checks and monitoring

**Configuration**:
- `FUZZY_SCORE_CUTOFF`: Used for plant name mapping (default: 85)
- Expected Excel columns:
  - `product_name`: Name of product
  - `scientific_name`: Plant scientific name
  - `disease_common_name`: Disease common name
  - `disease_scientific_name`: Disease scientific name

### 8. Analyze Service (`app/services/analyze_service_v4.py`)

**Responsibility**: Plant disease detection and analysis

**Workflow**:
1. Receives plant image from API
2. Runs YOLO v8 model (`best.pt`)
3. Detects plant in image
4. Sends image + detection to OpenAI GPT-4
5. Gets detailed disease analysis
6. Extracts treatment recommendations
7. Returns results with products

**Key Dependencies**:
- YOLO model: `app/models/best.pt`
- OpenAI API: Requires `OPENAI_API_KEY`

### 9. Product Routes (`app/routes/product_routes.py`)

**Responsibility**: HTTP endpoints for product search

**Endpoints**:

1. **`GET /products/`**
   - Returns all products
   - No parameters
   - Response: List of products

2. **`GET /products/by-scientific-name/{disease_scientific_name}`**
   - Fuzzy search for products
   - Query Parameters:
     - `plant_scientific_name` (optional): Filter by plant
   - Response: Top 3 matching products
   - **Most Used Endpoint**

3. **`GET /products/by-disease/{disease_name}`**
   - Filter by disease name
   - Response: Matching products

---

## Database Schema

### products table

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    product_name VARCHAR NOT NULL,
    scientific_name VARCHAR,
    disease_common_name VARCHAR,
    disease_scientific_name VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_disease_scientific_name ON products(disease_scientific_name);
CREATE INDEX idx_scientific_name ON products(scientific_name);
CREATE INDEX idx_product_name ON products(product_name);
```

### detection_history table

```sql
CREATE TABLE detection_history (
    id SERIAL PRIMARY KEY,
    image_path VARCHAR NOT NULL,
    detected_plant VARCHAR,
    detected_disease VARCHAR,
    confidence FLOAT,
    analysis_result TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### otp table

```sql
CREATE TABLE otp (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR UNIQUE NOT NULL,
    otp_code VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);
```

---

## API Endpoints

### Core Endpoints

#### 1. Health Check
```
GET /health
Response:
{
    "status": "healthy",
    "database": "connected",
    "products_loaded": true,
    "product_stats": {
        "total_products": 181,
        "unique_diseases": 76,
        "unique_plants": 10
    }
}
```

#### 2. Root Endpoint
```
GET /
Response:
{
    "status": "Plant Disease Detection API v4.2.0",
    "message": "API is running successfully"
}
```

#### 3. Product Search (Fuzzy)
```
GET /products/search?disease_scientific_name=powdery%20mildew&plant_scientific_name=Rosa
Query Parameters:
  - disease_scientific_name: str (required if plant_scientific_name not provided)
  - plant_scientific_name: str (optional)

Response:
[
    {
        "id": 1,
        "product_name": "ProductName",
        "scientific_name": "Rosa",
        "disease_common_name": "Powdery Mildew",
        "disease_scientific_name": "Podosphaera pannosa"
    },
    ...
]
```

#### 4. Get All Products
```
GET /products/
Response: List of all products
```

#### 5. Get Products by Disease
```
GET /products/by-disease/{disease_name}
Path Parameter:
  - disease_name: str

Response: List of products for that disease
```

#### 6. Analyze Image (Detect Disease)
```
POST /analyze
Body: multipart/form-data
  - file: Image file

Response:
{
    "detected_plant": "Rose",
    "detected_disease": "Powdery Mildew",
    "confidence": 0.95,
    "analysis": "Detailed AI analysis of the disease",
    "recommendations": [
        {
            "product": "Product Name",
            "reason": "Recommended because..."
        }
    ]
}
```

---

## Configuration

### Environment Variables (`.env`)

**Critical Variables**:

```bash
# Database Connection
DATABASE_URL=postgresql://user:pass@host:5432/db

# API Keys
OPENAI_API_KEY=sk-proj-...      # OpenAI GPT-4 API key
JWT_SECRET=garden_genie          # JWT signing secret

# External Services
AWS_ACCESS_KEY_ID=...            # AWS S3 access
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=ap-south-1
AWS_BUCKET_NAME=gardengenieimages

# SMS Service (E2A)
E2A_API_KEY=...
E2A_SENDER_ID=...
E2A_API_URL=...
E2A_ENTITY_ID=...
E2A_TEMPLATE_ID=...

# Fuzzy Matching Configuration
FUZZY_SCORE_CUTOFF=85            # Minimum match score (0-100)
FUZZY_WEIGHT_DISEASE=0.6         # Disease search weight
FUZZY_WEIGHT_PLANT=0.4           # Plant search weight
```

**Note**: `.env` is in `.gitignore` for security. Never commit it!

---

## Recent Changes & Improvements

### Latest Update (November 19, 2025)

#### Changes Made:

1. **Created Utility Modules** (New)
   - `app/services/match_utils.py`: Fuzzy string matching with caching
   - `app/services/product_cache.py`: In-memory product caching

2. **Updated Application Startup** (`app/main.py`)
   - Implemented asynccontextmanager lifespan for proper initialization
   - Added startup logging with visual indicators
   - Added `/health` endpoint for monitoring
   - Database tables creation moved to startup
   - Product import integrated into startup
   - Cache loading on startup

3. **Enhanced Product Import Service** (`app/services/product_import_service.py`)
   - Fixed SQLAlchemy transaction management (nested transaction issue)
   - Now uses `session.begin()` for proper ACID compliance
   - Added fuzzy matching for plant name mapping
   - Unmapped plant logging to CSV file
   - Better error handling with logging

4. **Updated Product Controller** (`app/controllers/product_controller.py`)
   - Converted to FastAPI-style with APIRouter
   - Implemented weighted fuzzy search
   - Returns top 3 results ranked by relevance
   - Added configurable scoring thresholds
   - Better error messages and logging

5. **Updated Environment Configuration** (`.env`)
   - Added fuzzy matching parameters:
     - `FUZZY_SCORE_CUTOFF=85`
     - `FUZZY_WEIGHT_DISEASE=0.6`
     - `FUZZY_WEIGHT_PLANT=0.4`

#### Improvements:

✅ **Performance**: In-memory caching eliminates database queries for searches  
✅ **Search Quality**: Fuzzy matching finds partial matches, improves UX  
✅ **Reliability**: Fixed transaction handling issues, better error management  
✅ **Configurability**: Tunable search parameters via environment variables  
✅ **Monitoring**: Added health check endpoint for deployment monitoring  
✅ **Code Quality**: Modular services, clear separation of concerns  
✅ **Logging**: Comprehensive logging for debugging and monitoring  

#### Breaking Changes:

⚠️ **Removed**: `/uploads` static file endpoint (to save storage in Docker)
- If your APK directly accessed `http://api/uploads/image.jpg`, it will break
- Image analysis still works, only direct URL access to uploads removed

### Version History

- **v4.2.0** (Current) - Production ready with fuzzy search & caching
- **v4.1.0** - Docker integration
- **v4.0.0** - Initial FastAPI port from Flask
- **v3.x** - Flask-based backend (deprecated)

---

## Development Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Git
- Virtual environment (venv)

### Local Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd Genie_AI_Backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create .env file
cp .env.example .env
# Edit .env with your configuration

# 6. Run application
python -m uvicorn app.main:app --reload

# 7. Open browser
# API Documentation: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

### Running Tests

```bash
# Run unit tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test
pytest tests/test_product_search.py
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

---

## Deployment

### Docker Deployment

```bash
# Build image
docker build -t genie-ai:latest .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL="..." \
  -e OPENAI_API_KEY="..." \
  genie-ai:latest

# Using Docker Compose
docker-compose up -d
docker-compose logs -f app

# Stop containers
docker-compose down
```

### Environment Variables for Deployment

```bash
# Database (use managed cloud service in production)
DATABASE_URL=postgresql://user:password@host:5432/plant_detection

# APIs
OPENAI_API_KEY=sk-proj-...
JWT_SECRET=<secure-random-string>

# AWS (for image storage)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=ap-south-1
AWS_BUCKET_NAME=gardengenieimages

# Fuzzy matching (tune for your use case)
FUZZY_SCORE_CUTOFF=85
FUZZY_WEIGHT_DISEASE=0.6
FUZZY_WEIGHT_PLANT=0.4
```

### AWS Deployment Checklist

- [ ] RDS PostgreSQL database created
- [ ] Database URL configured in environment
- [ ] OpenAI API key configured
- [ ] AWS S3 bucket created for image storage
- [ ] AWS credentials configured
- [ ] Environment variables set in deployment
- [ ] CORS settings appropriate for production
- [ ] Database backups configured
- [ ] Monitoring and logging set up
- [ ] Rate limiting configured (if needed)

---

## Known Issues & Limitations

### Current Issues

1. **Plant Map Excel File Required**
   - `Plant_Map.xlsx` must exist in root directory for product import
   - If missing, import fails silently
   - **Fix**: Add error message when file is missing

2. **YOLO Model Size**
   - `best.pt` is ~200MB, increases Docker image size
   - **Solution**: Use lighter model or lazy loading

3. **Memory Usage**
   - 181 products in cache is small, but scales linearly
   - With 10k products, cache would use ~50-100MB
   - **Solution**: Implement cache pagination if needed

4. **No Database Connection Pooling**
   - Current setup uses basic connections
   - Under high load, might exhaust connections
   - **Solution**: Configure connection pool in SQLAlchemy

### Limitations

- APK must be updated if API contract changes
- Fuzzy matching works best for close spelling
- YOLO model trained on specific plant dataset
- Requires internet for OpenAI API calls
- No offline analysis capability

---

## Future Roadmap

### Short Term (Next 1-2 months)

- [ ] Add database connection pooling
- [ ] Implement rate limiting
- [ ] Add request/response caching headers
- [ ] Comprehensive API documentation
- [ ] Unit and integration tests
- [ ] Performance benchmarking

### Medium Term (2-6 months)

- [ ] GraphQL API alongside REST
- [ ] WebSocket support for real-time analysis
- [ ] User authentication system
- [ ] Product recommendations based on history
- [ ] Batch image processing
- [ ] Custom model training pipeline

### Long Term (6+ months)

- [ ] Mobile app backend (push notifications)
- [ ] Marketplace integration for products
- [ ] Payment gateway integration
- [ ] Machine learning pipeline improvements
- [ ] Multi-language support
- [ ] Global scaling (CDN, multi-region)

---

## Troubleshooting Guide

### Issue: `Database connection error`
```
ERROR: This connection has already initialized a SQLAlchemy Transaction()
```
**Cause**: Nested transaction blocks in code  
**Solution**: Use `with session.begin():` instead of nested `with connection.begin()`

### Issue: `Products not loading`
```
ERROR: Failed to load products into cache
```
**Cause**: Database connection issues or missing products table  
**Solution**: Check DATABASE_URL, verify database is running, check table exists

### Issue: `YOLO model not found`
```
FileNotFoundError: app/models/best.pt not found
```
**Cause**: Model weights not downloaded  
**Solution**: Download from [Ultralytics](https://github.com/ultralytics/yolov8) and place in `app/models/`

### Issue: `OpenAI API errors`
```
AuthenticationError: Invalid API key
```
**Cause**: Invalid or expired OpenAI key  
**Solution**: Update OPENAI_API_KEY in .env, verify key has required permissions

### Issue: `Fuzzy search returns no results`
**Cause**: Search score below FUZZY_SCORE_CUTOFF  
**Solution**: Adjust FUZZY_SCORE_CUTOFF lower (75 instead of 85) in .env

---

## Quick Reference

### Database Connection
```python
from app.config.db import get_db

@app.get("/items")
def get_items(db: Session = Depends(get_db)):
    return db.query(Product).all()
```

### Using Product Cache
```python
from app.services.product_cache import get_cached_products

products = get_cached_products()  # Fast memory access
```

### Fuzzy Matching
```python
from app.services.match_utils import fuzzy_lookup, normalize

query = "powdery mildew"
choices = ("powdery mildew", "downy mildew", "leaf spot")
result = fuzzy_lookup(query, tuple(choices), score_cutoff=80)
# Returns: ("powdery mildew", 100, 0)
```

### Environment Variables
```python
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
score_cutoff = int(os.getenv("FUZZY_SCORE_CUTOFF", 85))
```

---

## Contact & Support

For questions or issues:
- Check existing issues in repository
- Review this documentation
- Check API docs at `/docs` when running
- Review logs for detailed error messages

---

**Document Version**: 1.0  
**Last Updated**: November 19, 2025  
**Maintained By**: Development Team  
**Next Review**: December 19, 2025
