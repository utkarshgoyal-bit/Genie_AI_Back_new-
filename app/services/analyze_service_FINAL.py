from ultralytics import YOLO
import os
import base64
import json
import time
import openai
from pathlib import Path
from dotenv import load_dotenv
from .image_utils import optimize_image, detect_image_type

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

MODEL_NAME = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o")
MAX_TOKENS = int(os.getenv("ANALYZER_MAX_TOKENS", "300"))
TEMPERATURE = float(os.getenv("ANALYZER_TEMPERATURE", "0.0"))

try:
    model = YOLO("app/models/best.pt")
    print("✅ YOLO model loaded successfully")
except Exception as e:
    print(f"❌ Failed to load YOLO model: {e}")
    raise RuntimeError(f"Failed to load YOLO model: {e}")

api_key = os.getenv("OPENAI_API_KEY")
print(f"🔑 API Key found: {api_key is not None}")
if api_key:
    print(f"🔑 API Key starts with: {api_key[:15]}...")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY environment variable required")

client = openai.OpenAI(api_key=api_key)
print("✅ OpenAI client initialized")

async def analyze_images(images: list[bytes]) -> dict:
    """
    IMPROVED VERSION: 
    - Always uses Image 2 (close-up/problem area) for YOLO detection
    - Handles non-plant images gracefully
    - Returns proper error for plants outside MVP scope
    """
    start_time = time.time()

    # Step 1: Optimize all images
    print(f"📸 Processing {len(images)} images...")

    optimized_images = []
    for idx, img_bytes in enumerate(images):
        img_type = detect_image_type(img_bytes)
        optimized = optimize_image(img_bytes, img_type)
        optimized_images.append(optimized)
        print(f"  ✓ Image {idx+1}: {img_type}, reduced {len(img_bytes)} → {len(optimized)} bytes")

    # Step 2: Always use Image 2 (close-up/problem area) for YOLO detection
    if len(optimized_images) >= 2:
        yolo_image = optimized_images[1]  # Always use second image (index 1)
        selected_idx = 1
        print(f"🎯 Using Image 2 (close-up/problem area) for YOLO detection")
    else:
        yolo_image = optimized_images[0]  # Fallback if only 1 image
        selected_idx = 0
        print(f"⚠️  Only 1 image provided, using it for YOLO detection")

    # Step 3: YOLO Detection
    print("🔍 Running YOLO plant detection...")
    with open("/tmp/temp_detect.jpg", "wb") as f:
        f.write(yolo_image)

    yolo_results = model("/tmp/temp_detect.jpg", verbose=False)
    detections = yolo_results[0].boxes

    if len(detections) == 0:
        return {
            "success": False,
            "error": "No plant detected in the images. Please ensure both images clearly show the plant.",
            "error_type": "no_detection",
            "yolo_time": round(time.time() - start_time, 2)
        }

    # Get highest confidence detection
    confidences = detections.conf.cpu().numpy()
    best_idx = confidences.argmax()
    plant_class_id = int(detections.cls[best_idx].item())
    plant_confidence = float(confidences[best_idx])

    class_name = model.names[plant_class_id]
    print(f"✅ YOLO detected: {class_name} ({plant_confidence:.2%} confidence)")

    # Check if confidence is too low (likely wrong detection)
    if plant_confidence < 0.60:  # 60% threshold
        print(f"⚠️  Low confidence detection ({plant_confidence:.2%}) - likely not a plant")
        return {
            "success": False,
            "error": "Unable to clearly identify the plant. Please upload clearer images showing the entire plant and affected areas.",
            "error_type": "low_confidence",
            "detected_class": class_name,
            "confidence": plant_confidence,
            "yolo_time": round(time.time() - start_time, 2)
        }

    # Step 4: Prepare all images for OpenAI analysis
    print(f"🤖 Sending {len(optimized_images)} images to OpenAI for diagnosis...")

    image_contents = []
    for idx, img_bytes in enumerate(optimized_images):
        base64_image = base64.b64encode(img_bytes).decode("utf-8")
        image_contents.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
        })

    # Step 5: Diagnostic Funnel Prompt
    prompt = f"""You are an expert plant pathologist. Analyze ALL provided images of this {class_name} plant.

DIAGNOSTIC FUNNEL (check in this order):
1. Plant Identification: Confirm species (scientific + common name)
2. Holistic Assessment: Overall health, growth stage, environment clues
3. Abiotic Stress FIRST: Check water, light, nutrients, temperature
4. Biotic Issues: Only if abiotic factors ruled out - fungal, bacterial, pest
5. Care Recommendations: Specific, actionable steps

CRITICAL: Prioritize environmental/cultural issues over diseases. Most problems are abiotic.

IMPORTANT: If you cannot identify a plant in the images, return this exact JSON:
{{"error": "no_plant_found", "message": "Unable to identify plant in images"}}

Output strict JSON (no markdown):
{{
  "plant_scientific_name": "Genus species",
  "plant_common_name": "Common name",
  "plant_confidence": {plant_confidence},
  "disease": "Specific issue name (e.g., Nitrogen Deficiency, Black Spot, Healthy)",
  "disease_scientific_name": "Scientific pathogen name if biotic, otherwise null",
  "disease_confidence": 0.0-1.0,
  "diagnosis_type": "abiotic|biotic|healthy",
  "symptoms": ["concise", "observed", "symptoms"],
  "cause": "Root cause explanation",
  "treatment": ["actionable", "prioritized", "steps"],
  "prevention": ["future", "care", "tips"]
}}

Be concise. No filler. Evidence-based only."""

    # Step 6: OpenAI API Call
    openai_start = time.time()

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{
                "role": "user",
                "content": [{"type": "text", "text": prompt}] + image_contents
            }],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE
        )

        openai_time = round(time.time() - openai_start, 2)
        print(f"✅ OpenAI response received ({openai_time}s)")

        raw_response = response.choices[0].message.content.strip()
        print(f"📝 Raw OpenAI response: {raw_response[:200]}...")  # Log first 200 chars

        # Parse JSON (handle markdown code blocks)
        if raw_response.startswith("```"):
            raw_response = raw_response.split("```")[1]
            if raw_response.startswith("json"):
                raw_response = raw_response[4:]
        
        raw_response = raw_response.strip()

        # Try to parse JSON
        try:
            diagnosis = json.loads(raw_response)
        except json.JSONDecodeError:
            # OpenAI returned plain text (couldn't identify plant)
            print(f"⚠️  OpenAI returned non-JSON response (likely no plant found)")
            return {
                "success": False,
                "error": "Unable to identify a plant in the provided images. Please ensure images clearly show the plant.",
                "error_type": "no_plant_identified",
                "openai_response": raw_response[:200],  # First 200 chars for debugging
                "yolo_time": round(time.time() - start_time - openai_time, 2),
                "openai_time": openai_time
            }

        # Check if OpenAI returned an error response
        if "error" in diagnosis and diagnosis.get("error") == "no_plant_found":
            return {
                "success": False,
                "error": diagnosis.get("message", "Unable to identify plant in images"),
                "error_type": "no_plant_identified",
                "yolo_time": round(time.time() - start_time - openai_time, 2),
                "openai_time": openai_time
            }

        # Add metadata
        diagnosis["success"] = True
        diagnosis["yolo_time"] = round(time.time() - start_time - openai_time, 2)
        diagnosis["openai_time"] = openai_time
        diagnosis["total_time"] = round(time.time() - start_time, 2)
        diagnosis["images_analyzed"] = len(images)
        diagnosis["yolo_image_used"] = selected_idx + 1  # 1-indexed for clarity

        print(f"✅ Total analysis time: {diagnosis['total_time']}s")
        print(f"✅ Diagnosis complete:")
        print(f"  Plant: {diagnosis.get('plant_common_name')} ({diagnosis.get('plant_scientific_name')})")
        print(f"  Issue: {diagnosis.get('disease')}")
        
        return diagnosis

    except json.JSONDecodeError as e:
        print(f"❌ JSON Parse Error: {e}")
        print(f"Raw response: {raw_response}")
        return {
            "success": False,
            "error": "Failed to get a valid diagnosis. Please try again with clearer images.",
            "error_type": "parse_error",
            "raw_response": raw_response[:200]
        }
    except Exception as e:
        print(f"❌ OpenAI API Error: {e}")
        return {
            "success": False,
            "error": f"Analysis service error: {str(e)}",
            "error_type": "api_error"
        }