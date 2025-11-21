#!/usr/bin/env python3
"""
E2E Test: Product Recommendation in Analyze Endpoint
Tests both direct function call and HTTP endpoint
"""
import sys
sys.path.insert(0, 'D:\\GitProjects\\Genie_AI_Backend')

import os
import json
import time
import glob

print("\n" + "="*70)
print("[TEST] PRODUCT RECOMMENDATION END-TO-END TEST")
print("="*70)

# ============================================================================
# Test 1: Direct Function Call (No HTTP)
# ============================================================================
print("\n[TEST 1] Direct fuzzy matching function")
print("-" * 70)

from app.controllers.product_controller_FINAL import find_product_by_diagnosis
from app.controllers.otp_controller import create_access_token
from app.config.db import SessionLocal

plant_scientific_name = "Rosa"
plant_common_name = "Rose"
disease_name = "Black Spot"

with SessionLocal() as db:
    result = find_product_by_diagnosis(
        plant_scientific_name, 
        plant_common_name, 
        disease_name, 
        db, 
        threshold=0.70
    )
    
    if result:
        print("[OK] SUCCESS: Product recommendation found!")
        print(f"   Product: {result['product_name']}")
        print(f"   Confidence: {result['match_confidence']:.1%}")
        print(f"   Disease Match: {result['disease']}")
    else:
        print("[FAIL] No product recommendation found")
        
print(f"\nFull response:\n{json.dumps(result, indent=2)}")

# ============================================================================
# Test 2: HTTP Endpoint Test
# ============================================================================
print("\n[TEST 2] HTTP /analyze endpoint with product recommendation")
print("-" * 70)

try:
    import urllib.request
    import urllib.error
    import base64
    
    # Generate JWT
    token = create_access_token({"sub": "+919999999999"})
    print(f"[OK] Generated JWT token")
    
    # Find sample image
    uploads_dir = "D:\\GitProjects\\Genie_AI_Backend\\uploads"
    sample_images = glob.glob(os.path.join(uploads_dir, "*.jpg")) + glob.glob(os.path.join(uploads_dir, "*.jpeg"))
    
    if not sample_images:
        print(f"[FAIL] No sample images found in {uploads_dir}")
        sys.exit(1)
    
    sample_image_path = sample_images[0]
    print(f"[OK] Using sample image: {os.path.basename(sample_image_path)}")
    
    # Prepare multipart form data manually
    boundary = '----WebKitFormBoundary' + os.urandom(16).hex()
    
    with open(sample_image_path, 'rb') as f:
        image_data = f.read()
    
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="images"; filename="{os.path.basename(sample_image_path)}"\r\n'
        f'Content-Type: image/jpeg\r\n\r\n'
    ).encode() + image_data + f'\r\n--{boundary}--\r\n'.encode()
    
    print(f"[OK] Prepared multipart request ({len(body)} bytes)")
    
    # Send request
    url = "http://127.0.0.1:8000/analyze"
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': f'multipart/form-data; boundary={boundary}'
        },
        method='POST'
    )
    
    print(f"[WAIT] Sending POST request to {url}...")
    start = time.time()
    
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            response_data = response.read()
            elapsed = time.time() - start
            
            try:
                result_json = json.loads(response_data)
                
                print(f"[OK] SUCCESS: Received response in {elapsed:.1f}s")
                print(f"\n[INFO] Response Summary:")
                print(f"   Detection ID: {result_json.get('detection_id')}")
                print(f"   Plant: {result_json.get('plant', {}).get('common_name')}")
                print(f"   Disease: {result_json.get('diagnosis', {}).get('disease')}")
                print(f"   Images uploaded: {result_json.get('images', {}).get('uploaded', 0)}")
                
                recommended = result_json.get('recommended_product')
                if recommended:
                    print(f"\n[SUCCESS] RECOMMENDED PRODUCT:")
                    print(f"   Name: {recommended.get('product_name')}")
                    print(f"   Disease: {recommended.get('disease')}")
                    print(f"   Confidence: {recommended.get('match_confidence'):.1%}")
                    print(f"\n*** PRODUCT RECOMMENDATION SUCCESSFULLY RETURNED! ***")
                else:
                    print(f"\n[WARN] No product recommendation in response")
                
                print(f"\n[INFO] Full Response:")
                print(json.dumps(result_json, indent=2)[:1000])  # First 1000 chars
                
            except json.JSONDecodeError as e:
                print(f"[FAIL] Failed to parse response as JSON: {e}")
                print(f"Raw response (first 500 chars): {response_data[:500]}")
    
    except urllib.error.URLError as e:
        print(f"[FAIL] Connection error: {e}")
        print(f"   Reason: {e.reason}")
    except urllib.error.HTTPError as e:
        print(f"[FAIL] HTTP error: {e.code}")
        response_data = e.read()
        try:
            error_json = json.loads(response_data)
            print(f"   Response: {json.dumps(error_json, indent=2)}")
        except:
            print(f"   Response: {response_data[:500]}")
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        import traceback
        traceback.print_exc()

except ImportError as e:
    print(f"[FAIL] Import error: {e}")
    
print("\n" + "="*70 + "\n")
