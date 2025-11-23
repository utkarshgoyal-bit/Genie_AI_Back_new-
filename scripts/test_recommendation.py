from app.controllers.product_controller import find_product_by_diagnosis
from app.controllers.otp_controller import create_access_token
from app.config.db import SessionLocal
import json
import os
import glob
import requests

print("\n" + "="*60)
print("🧪 PRODUCT RECOMMENDATION TEST")
print("="*60)

# Test 1: Direct function call
print("\n1️⃣  Testing direct function call with fuzzy matching...")
plant_scientific_name = "Rosa"
plant_common_name = "Rose"
disease_name = "Black Spot"

with SessionLocal() as db:
    result = find_product_by_diagnosis(plant_scientific_name, plant_common_name, disease_name, db, threshold=0.70)
    print(f"Result: {json.dumps(result, default=str, indent=2)}")
    if result:
        print("✅ Product recommendation working correctly!")
    else:
        print("⚠️  No product recommendation found")

# Test 2: Analyze endpoint E2E test
print("\n2️⃣  Testing /analyze endpoint E2E...")
JWT_SECRET = os.getenv("JWT_SECRET", "garden_genie")
mobile = "+919999999999"
token = create_access_token({"sub": mobile})
print(f"Generated JWT token: {token[:50]}...")

# Find a sample image in uploads/
uploads_dir = "D:\\GitProjects\\Genie_AI_Backend\\uploads"
sample_images = glob.glob(os.path.join(uploads_dir, "*.jpg")) + glob.glob(os.path.join(uploads_dir, "*.jpeg")) + glob.glob(os.path.join(uploads_dir, "*.png"))

if sample_images:
    sample_image = sample_images[0]
    print(f"Using sample image: {sample_image}")
    
    try:
        with open(sample_image, "rb") as f:
            files = {"images": f}
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.post("http://127.0.0.1:8000/analyze", files=files, headers=headers, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✅ Analyze endpoint success!")
                print(f"Recommended product: {result.get('recommended_product')}")
                if result.get('recommended_product'):
                    print("✅ PRODUCT RECOMMENDATION RETURNED IN RESPONSE!")
                else:
                    print("⚠️  No product recommendation in response")
            else:
                print(f"\n❌ Analyze endpoint failed: {response.status_code}")
                print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Error calling analyze endpoint: {e}")
else:
    print(f"⚠️  No sample images found in {uploads_dir}")

print("\n" + "="*60 + "\n")
