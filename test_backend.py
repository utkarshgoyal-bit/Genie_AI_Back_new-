#!/usr/bin/env python3
"""
GardenGenie Backend Test Script
================================
Tests backend functionality without starting the full FastAPI server.

Two modes:
1. PRODUCT MAPPING ONLY (no API key needed)
2. FULL ANALYSIS (requires OpenAI API key)
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# ============================================================================
# MODE 1: TEST PRODUCT MAPPING (NO API KEY NEEDED)
# ============================================================================

def test_product_mapping():
    """
    Tests fuzzy product matching without requiring OpenAI API key
    """
    print("\n" + "="*70)
    print("MODE 1: TESTING PRODUCT MAPPING (No API key needed)")
    print("="*70)

    from app.config.db import SessionLocal
    from app.controllers.product_controller_FINAL import find_product_by_diagnosis

    # Create database session
    db = SessionLocal()

    try:
        # Test Case 1: Rose with Black Spot
        print("\n📋 Test Case 1: Rose with Black Spot")
        print("-" * 70)
        result = find_product_by_diagnosis(
            plant_scientific_name="Rosa",
            plant_common_name="Rose",
            disease_name="Black Spot",
            db=db,
            threshold=0.70
        )

        if result:
            print(f"✅ Match found!")
            print(f"   Product: {result['product_name']}")
            print(f"   Confidence: {result['match_confidence']:.2%}")
            print(f"   Match type: {result['match_type']}")
        else:
            print("❌ No match found (threshold not met or no products in DB)")

        # Test Case 2: Tomato with Nitrogen Deficiency
        print("\n📋 Test Case 2: Tomato with Nitrogen Deficiency")
        print("-" * 70)
        result = find_product_by_diagnosis(
            plant_scientific_name="Solanum lycopersicum",
            plant_common_name="Tomato",
            disease_name="Nitrogen Deficiency",
            db=db,
            threshold=0.70
        )

        if result:
            print(f"✅ Match found!")
            print(f"   Product: {result['product_name']}")
            print(f"   Confidence: {result['match_confidence']:.2%}")
            print(f"   Match type: {result['match_type']}")
        else:
            print("❌ No match found (threshold not met or no products in DB)")

        # Test Case 3: Unknown plant/disease combo
        print("\n📋 Test Case 3: Unknown combination")
        print("-" * 70)
        result = find_product_by_diagnosis(
            plant_scientific_name="Plantus unknownus",
            plant_common_name="Mystery Plant",
            disease_name="Mysterious Ailment",
            db=db,
            threshold=0.70
        )

        if result:
            print(f"✅ Match found (possibly false positive):")
            print(f"   Product: {result['product_name']}")
            print(f"   Confidence: {result['match_confidence']:.2%}")
        else:
            print("✅ No match found (expected for unknown combo)")

        print("\n" + "="*70)
        print("✅ PRODUCT MAPPING TESTS COMPLETE")
        print("="*70)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


# ============================================================================
# MODE 2: TEST FULL ANALYSIS (REQUIRES OPENAI API KEY)
# ============================================================================

def test_full_analysis():
    """
    Tests complete AI analysis pipeline including OpenAI GPT
    Requires OPENAI_API_KEY in .env
    """
    print("\n" + "="*70)
    print("MODE 2: TESTING FULL AI ANALYSIS (Requires OpenAI API key)")
    print("="*70)

    # Check for API key
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n❌ ERROR: OPENAI_API_KEY not found in .env")
        print("   This test requires a valid OpenAI API key.")
        print("   Add it to your .env file: OPENAI_API_KEY=sk-...")
        return

    print(f"\n✅ API Key found: {api_key[:20]}...")

    # Import after confirming API key exists
    import asyncio
    from app.services.analyze_service_FINAL import analyze_images

    # Load test images
    test_image_paths = [
        "test_images/plant1.jpg",  # Replace with actual test image paths
        "test_images/plant2.jpg"
    ]

    # Check if test images exist
    missing_images = [p for p in test_image_paths if not os.path.exists(p)]
    if missing_images:
        print(f"\n⚠️  WARNING: Test images not found:")
        for img in missing_images:
            print(f"   - {img}")
        print("\n   Creating placeholder instructions...")
        print("   Please add real plant images to test_images/ folder")
        return

    # Read images as bytes
    print(f"\n📸 Loading {len(test_image_paths)} test images...")
    image_bytes_list = []
    for path in test_image_paths:
        with open(path, 'rb') as f:
            image_bytes_list.append(f.read())
        print(f"   ✓ Loaded {path} ({len(image_bytes_list[-1])} bytes)")

    # Run analysis
    print("\n🤖 Running AI analysis...")
    print("-" * 70)

    async def run_test():
        result = await analyze_images(image_bytes_list)
        return result

    try:
        result = asyncio.run(run_test())

        if result.get("success"):
            print("\n✅ ANALYSIS SUCCESSFUL!")
            print("-" * 70)
            print(f"Plant: {result.get('plant_common_name')} ({result.get('plant_scientific_name')})")
            print(f"Plant Confidence: {result.get('plant_confidence'):.2%}")
            print(f"\nDiagnosis: {result.get('disease')}")
            print(f"Type: {result.get('diagnosis_type')}")
            print(f"Confidence: {result.get('disease_confidence'):.2%}")
            print(f"\nSymptoms: {', '.join(result.get('symptoms', []))}")
            print(f"\nCause: {result.get('cause')}")
            print(f"\nTreatment:")
            for step in result.get('treatment', []):
                print(f"  - {step}")
            print(f"\nPrevention:")
            for step in result.get('prevention', []):
                print(f"  - {step}")
            print(f"\nTiming:")
            print(f"  - YOLO: {result.get('yolo_time')}s")
            print(f"  - OpenAI: {result.get('openai_time')}s")
            print(f"  - Total: {result.get('total_time')}s")
            print(f"  - Images analyzed: {result.get('images_analyzed')}")
        else:
            print(f"\n❌ ANALYSIS FAILED: {result.get('error')}")
            if 'raw_response' in result:
                print(f"\nRaw response: {result['raw_response']}")

        print("\n" + "="*70)
        print("✅ FULL ANALYSIS TEST COMPLETE")
        print("="*70)

    except Exception as e:
        print(f"\n❌ ERROR during analysis: {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# MODE 3: TEST PRODUCT MAPPING WITH MOCK AI RESULTS
# ============================================================================

def test_product_mapping_with_mock_diagnosis():
    """
    Tests the complete flow from diagnosis to product recommendation
    Uses mock AI results (no API key needed)
    """
    print("\n" + "="*70)
    print("MODE 3: TESTING FULL FLOW WITH MOCK DIAGNOSIS (No API key)")
    print("="*70)

    from app.config.db import SessionLocal
    from app.controllers.product_controller_FINAL import find_product_by_diagnosis

    # Mock AI diagnosis results
    mock_diagnoses = [
        {
            "name": "Rose with Black Spot",
            "plant_scientific_name": "Rosa",
            "plant_common_name": "Rose",
            "disease": "Black Spot"
        },
        {
            "name": "Tomato with Early Blight",
            "plant_scientific_name": "Solanum lycopersicum",
            "plant_common_name": "Tomato",
            "disease": "Early Blight"
        },
        {
            "name": "Plant with Nitrogen Deficiency",
            "plant_scientific_name": "Generic Plant",
            "plant_common_name": "Common Plant",
            "disease": "Nitrogen Deficiency"
        }
    ]

    db = SessionLocal()

    try:
        for mock in mock_diagnoses:
            print(f"\n📋 Test: {mock['name']}")
            print("-" * 70)
            print(f"   Plant: {mock['plant_common_name']} ({mock['plant_scientific_name']})")
            print(f"   Disease: {mock['disease']}")

            result = find_product_by_diagnosis(
                plant_scientific_name=mock['plant_scientific_name'],
                plant_common_name=mock['plant_common_name'],
                disease_name=mock['disease'],
                db=db,
                threshold=0.70
            )

            if result:
                print(f"\n   ✅ Product recommendation found:")
                print(f"      Product: {result['product_name']}")
                print(f"      Match confidence: {result['match_confidence']:.2%}")
                print(f"      Match type: {result['match_type']}")
            else:
                print(f"\n   ❌ No product found (threshold not met)")

        print("\n" + "="*70)
        print("✅ MOCK DIAGNOSIS TESTS COMPLETE")
        print("="*70)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("GARDENGENIE BACKEND TEST SUITE")
    print("="*70)
    print("\nAvailable test modes:")
    print("  1. Product mapping only (no API key)")
    print("  2. Full AI analysis (requires API key)")
    print("  3. Full flow with mock diagnosis (no API key)")
    print("  4. Run all applicable tests")

    choice = input("\nEnter choice (1-4): ").strip()

    if choice == "1":
        test_product_mapping()
    elif choice == "2":
        test_full_analysis()
    elif choice == "3":
        test_product_mapping_with_mock_diagnosis()
    elif choice == "4":
        print("\n🚀 Running all tests...")
        test_product_mapping()
        test_product_mapping_with_mock_diagnosis()

        # Only run full analysis if API key exists
        from dotenv import load_dotenv
        load_dotenv()
        if os.getenv("OPENAI_API_KEY"):
            test_full_analysis()
        else:
            print("\n⚠️  Skipping full AI analysis (no API key found)")
    else:
        print("\n❌ Invalid choice. Please run again with 1-4.")
