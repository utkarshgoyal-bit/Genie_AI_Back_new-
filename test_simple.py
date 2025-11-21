import sys
import os
import json
import time

# Set PYTHONPATH
sys.path.insert(0, 'D:\\GitProjects\\Genie_AI_Backend')

# Test 1: Direct function call
print("\n" + "="*60)
print("🧪 PRODUCT RECOMMENDATION TEST")
print("="*60)

from app.controllers.product_controller_FINAL import find_product_by_diagnosis
from app.controllers.otp_controller import create_access_token
from app.config.db import SessionLocal

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

# Test 2: Try an HTTP request to analyze endpoint
print("\n2️⃣  Testing /analyze endpoint E2E...")
time.sleep(2)

try:
    import urllib.request
    import glob
    
    JWT_SECRET = os.getenv("JWT_SECRET", "garden_genie")
    mobile = "+919999999999"
    token = create_access_token({"sub": mobile})
    print(f"Generated JWT token: {token[:50]}...")
    
    # Find sample image
    uploads_dir = "D:\\GitProjects\\Genie_AI_Backend\\uploads"
    sample_images = glob.glob(os.path.join(uploads_dir, "*.jpg"))
    
    if sample_images:
        sample_image = sample_images[0]
        print(f"Using sample image: {os.path.basename(sample_image)}")
        
        # Prepare the request
        with open(sample_image, 'rb') as f:
            image_data = f.read()
        
        url = "http://127.0.0.1:8000/analyze"
        
        # Use curl via subprocess instead
        import subprocess
        
        curl_cmd = [
            'curl', '-X', 'POST',
            '-H', f'Authorization: Bearer {token}',
            '-F', f'images=@{sample_image}',
            url
        ]
        
        result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=120)
        
        print(f"\n✅ Analyze endpoint response:")
        try:
            response_json = json.loads(result.stdout)
            print(json.dumps(response_json, indent=2))
            
            if response_json.get('recommended_product'):
                print("\n✅ PRODUCT RECOMMENDATION RETURNED IN RESPONSE!")
                print(f"Recommended Product: {response_json['recommended_product']['product_name']}")
            else:
                print("\n⚠️  No product recommendation in response")
        except json.JSONDecodeError:
            print(result.stdout[:200])
            if result.stderr:
                print(f"Error: {result.stderr[:200]}")
    else:
        print(f"⚠️  No sample images found in {uploads_dir}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60 + "\n")
