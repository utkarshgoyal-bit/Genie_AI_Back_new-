import requests
import os
import json
import time
import re
from typing import Dict, Any
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def process_single_image(image_path: str, headers: dict, BASE_URL: str) -> dict:
    result = {
        "image_name": os.path.basename(image_path),
        "disease_detected": False,
        "products_found": False,
        "num_products": 0,
        "plant_name": None,
        "disease_name": None,
        "confidence": None,
        "status": "failed"
    }
    
    print(f"\n📝 Testing image: {result['image_name']}")
    print("-" * 50)
    
    # Check if file exists and is an image
    if not os.path.exists(image_path):
        print(f"❌ Image not found at {image_path}")
        return False
        
    if not image_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
        print(f"❌ Unsupported image format for {image_path}")
        return False

    # Read the image once
    with open(image_path, "rb") as img:
        image_data = img.read()
    
    # Test single image upload
    files = {"images": [(os.path.basename(image_path), image_data, "image/jpeg")]}
    analyze_response = requests.post(
        f"{BASE_URL}/analyze",
        files={"images": (os.path.basename(image_path), image_data, "image/jpeg")},
        headers=headers
    )
    
    if analyze_response.status_code != 200:
        print("❌ Image analysis failed!")
        print(analyze_response.json())
        return False
    
    analysis_result = analyze_response.json()["data"]
    result["disease_detected"] = True
    
    # Extract values, handling list formats
    common_name = analysis_result.get('common_name')
    scientific_name = analysis_result.get('scientific_name')
    disease = analysis_result.get('disease')
    disease_scientific_name = analysis_result.get('disease_scientific_name')
    confidence = analysis_result.get('disease_confidence')
    
    # Handle list formats
    if isinstance(disease, list): disease = disease[0]
    if isinstance(disease_scientific_name, list): disease_scientific_name = disease_scientific_name[0]
    if isinstance(confidence, list): confidence = confidence[0]
    
    # Remove any '%' from confidence
    if isinstance(confidence, str):
        confidence = confidence.replace('%', '')
    
    result["plant_name"] = f"{common_name} ({scientific_name})"
    result["disease_name"] = f"{disease} ({disease_scientific_name})"
    result["confidence"] = confidence
    result["scientific_name"] = scientific_name
    result["disease_scientific_name"] = disease_scientific_name
    
    print("\n🔍 Disease Detection Results:")
    print(f"Plant: {result['plant_name']}")
    print(f"Disease: {result['disease_name']}")
    print(f"Confidence: {result['confidence']}%")
    print("\nDebug Info:")
    print(f"Plant Scientific Name (for matching): {result['scientific_name']}")
    print(f"Disease Scientific Name (for matching): {result['disease_scientific_name']}")
    
    # Search for matching products
    disease_name = analysis_result.get("disease_scientific_name")
    plant_name = analysis_result.get("scientific_name")
    
    if not disease_name or not plant_name:
        print("❌ Missing disease or plant scientific names!")
        return False
        
    try:
        # Handle list format for disease_name and plant_name
        if isinstance(disease_name, list):
            disease_name = disease_name[0]  # Take first disease if multiple
        if isinstance(plant_name, list):
            plant_name = plant_name[0]  # Take first plant if multiple
            
        # Convert to strings
        disease_name = str(disease_name)
        plant_name = str(plant_name)
        
        print("\n🔍 Product Search Details:")
        print("1. Original Values:")
        print(f"   Disease Scientific Name: {disease_name}")
        print(f"   Plant Scientific Name: {plant_name}")
        
        # Normalize the search terms to match server-side processing
        normalized_disease = re.sub(r'[^a-z0-9\s]', '', disease_name.lower()).strip()
        normalized_plant = re.sub(r'[^a-z0-9\s]', '', plant_name.lower()).strip()
        
        print("\n2. Normalized Values (for fuzzy matching):")
        print(f"   Disease: {normalized_disease}")
        print(f"   Plant: {normalized_plant}")
        print("\n3. Search Configuration:")
        print("   • Using fuzzy matching with weighted scores")
        print("   • Disease match weight: 60%")
        print("   • Plant match weight: 40%")
        print("   • Required combined score: 85%")
        
        # Extract the disease name for URL path and encode it properly
        encoded_disease_name = requests.utils.quote(disease_name)
        
        print("\nMaking request to:")
        print(f"URL: {BASE_URL}/products/by-scientific-name/{encoded_disease_name}")
        print(f"Params: {{'plant_scientific_name': {plant_name}}}")
        
        url = f"{BASE_URL}/products/search"
        params = {
            "disease_scientific_name": disease_name,
            "plant_scientific_name": plant_name
        }
        print(f"\nFinal request URL: {url}")
        print(f"Query parameters: {params}")
        
        product_response = requests.get(
            url,
            params=params,
            headers=headers
        )
        
        if product_response.status_code == 404:
            print("\n⚠️ No matching products found")
            print("This means no products in the database match this disease and plant combination.")
            return True
        elif product_response.status_code != 200:
            print("❌ Product search failed!")
            print(f"Status code: {product_response.status_code}")
            try:
                print(product_response.json())
            except:
                print(f"Response text: {product_response.text}")
            return False
    except Exception as e:
        print(f"❌ Error during product search: {str(e)}")
        return False
    
    products = product_response.json()
    result["products_found"] = True
    result["num_products"] = len(products)
    result["status"] = "success"
    
    print("\n✅ Matching Products Found:")
    for idx, product in enumerate(products, 1):
        normalized_product_disease = re.sub(r'[^a-z0-9\s]', '', str(product.get('disease_scientific_name', '')).lower()).strip()
        normalized_product_plant = re.sub(r'[^a-z0-9\s]', '', str(product.get('scientific_name', '')).lower()).strip()
        
        print(f"\nProduct {idx}:")
        print(f"Name: {product.get('name')}")
        print(f"Target Disease: {product.get('disease_common_name')} ({product.get('disease_scientific_name')})")
        print(f"Target Plant: {product.get('common_name')} ({product.get('scientific_name')})")
        print("\nMatching Details:")
        print(f"Disease Normalized Comparison:")
        print(f"  Query: {normalized_disease}")
        print(f"  Product: {normalized_product_disease}")
        print(f"Plant Normalized Comparison:")
        print(f"  Query: {normalized_plant}")
        print(f"  Product: {normalized_product_plant}")
    
    # Add a small delay between requests to avoid overwhelming the server
    time.sleep(1)
    return result

def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,  # number of retries
        backoff_factor=1,  # wait 1, 2, 4 seconds between retries
        status_forcelist=[500, 502, 503, 504],  # status codes to retry on
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def show_available_products(BASE_URL: str, headers: dict):
    """Check what products are available in the database"""
    try:
        response = requests.get(f"{BASE_URL}/products", headers=headers)
        if response.status_code == 200:
            products = response.json()
            print("\n📦 Available Products in Database:")
            print("-" * 80)
            for idx, product in enumerate(products, 1):
                print(f"\nProduct {idx}:")
                print(f"Name: {product.get('name', 'N/A')}")
                print(f"Plant: {product.get('common_name', 'N/A')} ({product.get('scientific_name', 'N/A')})")
                print(f"Disease: {product.get('disease_common_name', 'N/A')} ({product.get('disease_scientific_name', 'N/A')})")
            print("-" * 80)
            return True
        else:
            print("\n❌ Failed to fetch products!")
            print(f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"\n❌ Error fetching products: {str(e)}")
        return False

def test_disease_product_matching():
    # Base URL - modify as needed for your environment
    BASE_URL = "http://localhost:8000"  # or your actual API URL
    
    # Create a session with retry logic
    session = create_session()
    
    # 1. First request an OTP
    test_mobile = input("Enter test mobile number: ")
    
    # Request OTP
    try:
        otp_request = session.post(f"{BASE_URL}/auth/send_otp", json={
            "mobile": test_mobile
        }, timeout=10)
        
        if otp_request.status_code != 200:
            print("❌ OTP request failed!")
            print(f"Status code: {otp_request.status_code}")
            try:
                print(otp_request.json())
            except:
                print(f"Response text: {otp_request.text}")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Connection error! Make sure the server is running at", BASE_URL)
        return
    except requests.exceptions.Timeout:
        print("❌ Request timed out! Server is taking too long to respond")
        return
    except Exception as e:
        print("❌ An error occurred:", str(e))
        return
    
    print("✅ OTP has been sent to your mobile")
    otp = input("Enter the OTP received: ")
    
    # Login with OTP
    try:
        auth_response = session.post(f"{BASE_URL}/auth/verify_otp", json={
            "mobile": test_mobile,
            "otp": otp
        }, timeout=10)
        
        if auth_response.status_code != 200:
            print("❌ Authentication failed!")
            print(f"Status code: {auth_response.status_code}")
            try:
                print(auth_response.json())
            except:
                print(f"Response text: {auth_response.text}")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Connection error! Make sure the server is running at", BASE_URL)
        return
    except requests.exceptions.Timeout:
        print("❌ Request timed out! Server is taking too long to respond")
        return
    except Exception as e:
        print("❌ An error occurred:", str(e))
        return
    
    token = auth_response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # First, let's check what products we have in the database
    if not show_available_products(BASE_URL, headers):
        print("❌ Could not verify product database. Continuing with tests anyway...")
    
    # 2. Get the test images folder path
    test_folder = input("Enter the path to the folder containing test images: ")
    folder_path = Path(test_folder)
    
    if not folder_path.exists() or not folder_path.is_dir():
        print(f"❌ Invalid folder path: {test_folder}")
        return
    
    # Get all image files from the folder
    image_files = [
        str(f) for f in folder_path.glob("*")
        if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']
    ]
    
    if not image_files:
        print(f"❌ No supported image files found in {test_folder}")
        return
    
    print(f"\n� Found {len(image_files)} image(s) to test")
    
    # Process each image
    successful_tests = 0
    total_tests = len(image_files)
    
    for image_path in image_files:
        if process_single_image(image_path, headers, BASE_URL):
            successful_tests += 1
        print("\n" + "="*70 + "\n")  # Separator between images
    
    # Print summary
    print("\n📊 Test Summary:")
    print(f"Total images tested: {total_tests}")
    print(f"Successful analyses: {successful_tests}")
    print(f"Failed analyses: {total_tests - successful_tests}")
    print(f"Success rate: {(successful_tests/total_tests)*100:.1f}%")

if __name__ == "__main__":
    test_disease_product_matching()