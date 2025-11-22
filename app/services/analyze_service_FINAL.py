from ultralytics import YOLO
import os
import base64
import json
import time
import re
import openai
from pathlib import Path
from dotenv import load_dotenv
from .image_utils import optimize_image, select_best_image, detect_image_type

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


def extract_json_from_response(raw_response: str) -> str:
    """
    Extract JSON from OpenAI response, handling:
    - Clean JSON
    - JSON wrapped in ```json``` code blocks
    - JSON with text before/after it
    """
    # Try to find JSON in markdown code block
    json_match = re.search(r'```json?\s*([\s\S]*?)\s*```', raw_response)
    if json_match:
        return json_match.group(1).strip()
    
    # If response already starts with {, it's clean JSON
    if raw_response.strip().startswith('{'):
        return raw_response.strip()
    
    # Find raw JSON object anywhere in response
    json_start = raw_response.find('{')
    if json_start != -1:
        # Find the matching closing brace
        brace_count = 0
        for i, char in enumerate(raw_response[json_start:]):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return raw_response[json_start:json_start + i + 1]
        # If no matching brace found, return from start to end
        return raw_response[json_start:]
    
    # No JSON found, return as-is (will fail at json.loads)
    return raw_response


async def analyze_images(images: list[bytes]) -> dict:
    """
    FINAL VERSION: Diagnostic Funnel approach with multi-image analysis
    - Uses all provided images for comprehensive diagnosis
    - Outputs both scientific and common names
    - Includes disease field for fuzzy matching
    """
    start_time = time.time()

    # Step 1: Smart image selection and optimization
    print(f"📸 Processing {len(images)} images...")

    optimized_images = []
    for idx, img_bytes in enumerate(images):
        img_type = detect_image_type(img_bytes)
        optimized = optimize_image(img_bytes, img_type)
        optimized_images.append(optimized)
        print(f"  ✓ Image {idx+1}: {img_type}, reduced {len(img_bytes)} → {len(optimized)} bytes")

    # Use best image for YOLO detection
    best_image, best_type, best_idx = select_best_image(optimized_images)
    print(f"🎯 Selected best image for YOLO detection")

    # Step 2: YOLO Detection
    print("🔍 Running YOLO plant detection...")
    with open("/tmp/temp_detect.jpg", "wb") as f:
        f.write(best_image)

    yolo_results = model("/tmp/temp_detect.jpg", verbose=False)
    detections = yolo_results[0].boxes

    if len(detections) == 0:
        return {
            "success": False,
            "error": "No plant detected in image",
            "yolo_time": round(time.time() - start_time, 2)
        }

    # Get highest confidence detection
    confidences = detections.conf.cpu().numpy()
    best_det_idx = confidences.argmax()
    plant_class_id = int(detections.cls[best_det_idx].item())
    plant_confidence = float(confidences[best_det_idx])

    class_name = model.names[plant_class_id]
    print(f"✅ YOLO detected: {class_name} ({plant_confidence:.2%} confidence)")

    # Step 3: Prepare all images for OpenAI analysis
    print(f"🤖 Sending {len(optimized_images)} images to OpenAI for diagnosis...")

    image_contents = []
    for idx, img_bytes in enumerate(optimized_images):
        base64_image = base64.b64encode(img_bytes).decode("utf-8")
        image_contents.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
        })

    # Step 4: Diagnostic Funnel Prompt
    prompt = f"""You are an expert plant pathologist. Analyze ALL provided images of this {class_name} plant.

DIAGNOSTIC FUNNEL (check in this order):
1. Plant Identification: Confirm species (scientific + common name)
2. Holistic Assessment: Overall health, growth stage, environment clues
3. Abiotic Stress FIRST: Check water, light, nutrients, temperature
4. Biotic Issues: Only if abiotic factors ruled out - fungal, bacterial, pest
5. Care Recommendations: Specific, actionable steps

CRITICAL: Prioritize environmental/cultural issues over diseases. Most problems are abiotic.

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

    # Step 5: OpenAI API Call
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

        # Parse JSON (handle text before/after code blocks)
        cleaned_json = extract_json_from_response(raw_response)
        diagnosis = json.loads(cleaned_json)

        # Add metadata
        diagnosis["success"] = True
        diagnosis["yolo_time"] = round(time.time() - start_time - openai_time, 2)
        diagnosis["openai_time"] = openai_time
        diagnosis["total_time"] = round(time.time() - start_time, 2)
        diagnosis["images_analyzed"] = len(images)

        print(f"✅ Total analysis time: {diagnosis['total_time']}s")
        return diagnosis

    except json.JSONDecodeError as e:
        print(f"❌ JSON Parse Error: {e}")
        print(f"Raw response: {raw_response}")
        return {
            "success": False,
            "error": "Failed to parse AI response",
            "raw_response": raw_response
        }
    except Exception as e:
        print(f"❌ OpenAI API Error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def analyze_images_direct(images: list[bytes]) -> dict:
    """
    DIRECT VERSION: Skips YOLO detection, OpenAI identifies plant + diagnoses.
    Used for /analyze/direct endpoint (no authentication required).
    """
    start_time = time.time()

    # Step 1: Optimize all images
    print(f"📸 Processing {len(images)} images (direct mode)...")

    optimized_images = []
    for idx, img_bytes in enumerate(images):
        img_type = detect_image_type(img_bytes)
        optimized = optimize_image(img_bytes, img_type)
        optimized_images.append(optimized)
        print(f"  ✓ Image {idx+1}: {img_type}, reduced {len(img_bytes)} → {len(optimized)} bytes")

    # Step 2: Prepare all images for OpenAI analysis
    print(f"🤖 Sending {len(optimized_images)} images to OpenAI (direct analysis)...")

    image_contents = []
    for idx, img_bytes in enumerate(optimized_images):
        base64_image = base64.b64encode(img_bytes).decode("utf-8")
        image_contents.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
        })

    # Step 3: Prompt for OpenAI (must identify plant + diagnose)
    prompt = """You are an expert plant pathologist. Analyze ALL provided images.

TASK: First IDENTIFY the plant, then DIAGNOSE any issues.

DIAGNOSTIC FUNNEL (check in this order):
1. Plant Identification: Determine species (scientific + common name) from visual features
2. Holistic Assessment: Overall health, growth stage, environment clues
3. Abiotic Stress FIRST: Check water, light, nutrients, temperature
4. Biotic Issues: Only if abiotic factors ruled out - fungal, bacterial, pest
5. Care Recommendations: Specific, actionable steps

CRITICAL: Prioritize environmental/cultural issues over diseases. Most problems are abiotic.

Output strict JSON (no markdown):
{
  "plant_scientific_name": "Genus species",
  "plant_common_name": "Common name",
  "plant_confidence": 0.0-1.0,
  "disease": "Specific issue name (e.g., Nitrogen Deficiency, Black Spot, Healthy)",
  "disease_scientific_name": "Scientific pathogen name if biotic, otherwise null",
  "disease_confidence": 0.0-1.0,
  "diagnosis_type": "abiotic|biotic|healthy",
  "symptoms": ["concise", "observed", "symptoms"],
  "cause": "Root cause explanation",
  "treatment": ["actionable", "prioritized", "steps"],
  "prevention": ["future", "care", "tips"]
}

If you cannot identify the plant, use "Unknown" for names and 0.0 for plant_confidence.
Be concise. No filler. Evidence-based only."""

    # Step 4: OpenAI API Call
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

        # Parse JSON (handle text before/after code blocks)
        cleaned_json = extract_json_from_response(raw_response)
        diagnosis = json.loads(cleaned_json)

        # Add metadata
        diagnosis["success"] = True
        diagnosis["yolo_time"] = 0  # No YOLO in direct mode
        diagnosis["openai_time"] = openai_time
        diagnosis["total_time"] = round(time.time() - start_time, 2)
        diagnosis["images_analyzed"] = len(images)
        diagnosis["mode"] = "direct"  # Flag to indicate direct mode

        print(f"✅ Total analysis time: {diagnosis['total_time']}s")
        return diagnosis

    except json.JSONDecodeError as e:
        print(f"❌ JSON Parse Error: {e}")
        print(f"Raw response: {raw_response}")
        return {
            "success": False,
            "error": "Failed to parse AI response",
            "raw_response": raw_response
        }
    except Exception as e:
        print(f"❌ OpenAI API Error: {e}")
        return {
            "success": False,
            "error": str(e)
        }