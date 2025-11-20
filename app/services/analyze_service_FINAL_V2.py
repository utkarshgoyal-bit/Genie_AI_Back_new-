from ultralytics import YOLO
import os
import base64
import json
import time
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
print(f"🔍 API Key found: {api_key is not None}")
if api_key:
    print(f"🔍 API Key starts with: {api_key[:15]}...")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY environment variable required")

client = openai.OpenAI(api_key=api_key)
print("✅ OpenAI client initialized")

async def analyze_images(images: list[bytes]) -> dict:
    """
    FINAL VERSION V2: Diagnostic Funnel with Python Enforcement
    - Uses all provided images for comprehensive diagnosis
    - Strict prompt for abiotic-first priority
    - Python post-processing to enforce rules if AI misbehaves
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
    best_image, image_type, selected_idx = select_best_image(optimized_images)
    print(f"🎯 Selected best image for YOLO detection (index: {selected_idx})")

    # Step 2: YOLO Detection
    # Step 2: YOLO Detection
    print("🔍 Running YOLO plant detection...")
    import tempfile
    import os
    
    # Use cross-platform temp directory
    temp_dir = tempfile.gettempdir()
    temp_image_path = os.path.join(temp_dir, "temp_detect.jpg")
    
    with open(temp_image_path, "wb") as f:
        f.write(best_image)

    yolo_results = model(temp_image_path, verbose=False)
    detections = yolo_results[0].boxes

    if len(detections) == 0:
        return {
            "success": False,
            "error": "No plant detected in image",
            "yolo_time": round(time.time() - start_time, 2)
        }

    # Get highest confidence detection
    confidences = detections.conf.cpu().numpy()
    best_idx = confidences.argmax()
    plant_class_id = int(detections.cls[best_idx].item())
    plant_confidence = float(confidences[best_idx])

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

    # Step 4: Diagnostic Funnel Prompt (V2 - Stricter Priority)
    prompt = f"""Plant pathologist analyzing {class_name}.

CHECK IN ORDER (stop at first match with confidence ≥60):

1. WATER: Overwatered (yellow, wilting) or Underwatered (crispy, drooping)?
2. LIGHT: Too much sun (burnt edges) or Too little (pale, leggy)?  
3. NUTRIENTS: N (pale yellow), Mg (vein yellowing), K (brown tips)?
4. PHYSICAL: Old age (lower leaves) or damage (tears)?
5. DISEASE: Fungal/bacterial ONLY if above all <60 AND this ≥80

RULE: Report highest priority issue ≥60. Disease needs ≥80 AND no abiotic ≥60.

JSON:
{{
  "plant_scientific_name": "Genus species",
  "plant_common_name": "Name",
  "plant_confidence": {plant_confidence},
  "disease": "Issue name (e.g. Nitrogen Deficiency, Leaf Spot)",
  "disease_scientific_name": "Scientific or null",
  "disease_confidence": 0.0-1.0,
  "diagnosis_type": "water|light|nutrient|physical|disease|healthy",
  "symptoms": ["2-3 key signs"],
  "cause": "Why (1 line)",
  "treatment": ["Steps"],
  "prevention": ["Tips"]
}}
"""

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

        # Parse JSON (handle markdown code blocks)
        if raw_response.startswith("```"):
            raw_response = raw_response.split("```")[1]
            if raw_response.startswith("json"):
                raw_response = raw_response[4:]

        diagnosis = json.loads(raw_response.strip())

        # ========================================================================
        # ENFORCEMENT LOGIC: Override AI if it violated diagnostic priority rules
        # ========================================================================
        
        diagnosis_type = diagnosis.get("diagnosis_type", "").lower()
        disease_conf = float(diagnosis.get("disease_confidence", 0))
        disease_name = diagnosis.get("disease", "").lower()
        symptoms_str = " ".join(diagnosis.get("symptoms", [])).lower()
        
        print(f"🔍 AI Output: disease='{disease_name}', type='{diagnosis_type}', confidence={disease_conf:.0%}")
        
        # RULE 1: Disease confidence must be ≥80% to be reported as disease
        if diagnosis_type == "disease" and disease_conf < 0.80:
            print(f"⚠️  OVERRIDE: Disease confidence {disease_conf:.0%} < 80%, reclassifying as physical issue")
            diagnosis["disease"] = "Natural Leaf Aging or Physical Damage"
            diagnosis["diagnosis_type"] = "physical"
            diagnosis["disease_scientific_name"] = None
            diagnosis["cause"] = "Lower leaves naturally age and brown in palms. This is normal plant maintenance."
            diagnosis["treatment"] = [
                "Trim brown/dead fronds at the base with clean shears",
                "Ensure bright indirect light (avoid direct sun)",
                "Maintain consistent watering schedule"
            ]
            diagnosis["prevention"] = [
                "Remove old fronds regularly",
                "Keep in filtered light location",
                "Maintain 50-60% humidity if possible"
            ]
        
        # RULE 2: Brown tips/burnt edges = Sun scorch (override if misclassified)
        elif ("brown tip" in symptoms_str or "burnt" in symptoms_str or "crispy edge" in symptoms_str or 
              "scorch" in symptoms_str or "sun damage" in symptoms_str):
            if diagnosis_type not in ["light"]:
                print(f"⚠️  OVERRIDE: Brown tips/burnt edges detected → Sun exposure issue")
                diagnosis["disease"] = "Sun Scorch / Excessive Light Exposure"
                diagnosis["diagnosis_type"] = "light"
                diagnosis["disease_scientific_name"] = None
                diagnosis["cause"] = "Direct sunlight causing leaf tip and edge burn. Areca palms need filtered light."
                diagnosis["treatment"] = [
                    "Relocate to area with bright indirect light",
                    "Trim severely damaged fronds",
                    "Avoid direct afternoon sun exposure"
                ]
                diagnosis["prevention"] = [
                    "Keep in bright but filtered light (near window with sheer curtain)",
                    "Rotate plant weekly for even light exposure",
                    "Monitor for new brown tips as early warning sign"
                ]
        
        # RULE 3: Yellow leaves + wilting = Water issue (override if misclassified)
        elif ("yellow" in symptoms_str and "wilt" in symptoms_str) or "drooping" in symptoms_str:
            if diagnosis_type not in ["water"]:
                print(f"⚠️  OVERRIDE: Yellowing + wilting detected → Water stress issue")
                diagnosis["disease"] = "Overwatering" if "yellow" in symptoms_str else "Underwatering"
                diagnosis["diagnosis_type"] = "water"
                diagnosis["disease_scientific_name"] = None
                diagnosis["cause"] = "Improper watering schedule causing root stress"
                diagnosis["treatment"] = [
                    "Check soil moisture before watering",
                    "Ensure pot has drainage holes",
                    "Water when top 1-2 inches of soil is dry"
                ]
                diagnosis["prevention"] = [
                    "Water consistently but allow soil to partially dry between waterings",
                    "Use well-draining potting mix",
                    "Avoid standing water in saucer"
                ]
        
        # RULE 4: Pale yellow new growth = Nutrient deficiency (override if misclassified)
        elif ("pale" in symptoms_str or "chlorosis" in symptoms_str) and "yellow" in symptoms_str:
            if diagnosis_type not in ["nutrient"]:
                print(f"⚠️  OVERRIDE: Pale yellowing detected → Nutrient deficiency")
                diagnosis["disease"] = "Nitrogen or Iron Deficiency"
                diagnosis["diagnosis_type"] = "nutrient"
                diagnosis["disease_scientific_name"] = None
                diagnosis["cause"] = "Lack of essential nutrients (nitrogen, iron, or magnesium)"
                diagnosis["treatment"] = [
                    "Apply balanced liquid fertilizer (20-20-20) diluted to half strength",
                    "Feed monthly during growing season",
                    "Consider iron supplement if new leaves affected"
                ]
                diagnosis["prevention"] = [
                    "Fertilize regularly March-September",
                    "Use palm-specific fertilizer if available",
                    "Ensure proper soil pH (6.0-7.0)"
                ]
        
        # RULE 5: If disease reported but symptoms match abiotic, force physical
        elif diagnosis_type == "disease" and disease_conf >= 0.80:
            # Check if symptoms actually suggest abiotic issue despite high confidence
            abiotic_keywords = ["brown tip", "yellow leaves", "wilting", "drooping", "pale", "crispy"]
            abiotic_match = any(kw in symptoms_str for kw in abiotic_keywords)
            
            if abiotic_match:
                print(f"⚠️  WARNING: Disease confidence high ({disease_conf:.0%}) but symptoms suggest abiotic issue")
                print(f"    Symptoms: {symptoms_str}")
                print(f"    Keeping disease diagnosis but flagging for review")
        
        print(f"✅ Final diagnosis: '{diagnosis.get('disease')}' (type: {diagnosis.get('diagnosis_type')})")

        # ========================================================================
        # END ENFORCEMENT LOGIC
        # ========================================================================

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