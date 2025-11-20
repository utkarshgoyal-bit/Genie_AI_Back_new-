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
    print("YOLO model loaded successfully")
except Exception as e:
    print(f"Failed to load YOLO model: {e}")
    raise RuntimeError(f"Failed to load YOLO model: {e}")

api_key = os.getenv("OPENAI_API_KEY")
print(f"API Key found: {api_key is not None}")
if api_key:
    print(f"API Key starts with: {api_key[:15]}...")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY environment variable required")

client = openai.OpenAI(api_key=api_key)
print("OpenAI client initialized")

PROMPT = (
    "Return EXACTLY one JSON object ONLY, matching these keys:"
    "common_name, scientific_name, plant_confidence, disease, disease_scientific_name,"
    "disease_confidence, symptoms, cause, treatment. "
    "All confidences=integers 0-100. Symptoms:2-3 words. Cause/treatment:1-2 lines. "
    "Abiotic-first: check water, light, temp, nutrients, soil/pH, mechanical, chemical. "
    "If any abiotic confidence>=60, set disease=[\"healthy\"], disease_confidence=[0] "
    "UNLESS a disease_confidence>=abiotic_confidence+20. Keep output compact (no extra fields). "
    "If uncertain use \"Unknown Plant\"/\"Species unknown\". Return the JSON now."
)


async def analyze_images(images: list[bytes]) -> dict:
    start_time = time.time()
    try:
        selected_image, image_type, selected_idx = select_best_image(images)
        optimized_image = optimize_image(selected_image, image_type)

        original_kb = len(selected_image) / 1024
        optimized_kb = len(optimized_image) / 1024
        reduction = ((original_kb - optimized_kb) / original_kb) * 100 if original_kb > 0 else 0
        print(f"Image {selected_idx + 1} selected ({image_type}): {original_kb:.1f}KB -> {optimized_kb:.1f}KB ({reduction:.1f}% reduction)")

        b64 = base64.b64encode(optimized_image).decode()
        content = [
            {"type": "text", "text": PROMPT},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
        ]

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": content}],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            response_format={"type": "json_object"}
        )

        raw = response.choices[0].message.content
        if isinstance(raw, (dict, list)):
            result = raw
        else:
            result = json.loads(raw)

        if not isinstance(result, dict):
            raise ValueError("OpenAI returned non-object JSON")

        required_fields = [
            "common_name", "scientific_name", "plant_confidence",
            "disease", "disease_scientific_name", "disease_confidence",
            "symptoms", "cause", "treatment"
        ]

        for k in required_fields:
            if k not in result or result[k] is None:
                result[k] = [] if k in ["disease", "disease_scientific_name", "disease_confidence", "symptoms", "cause", "treatment"] else ""

        if not result.get('common_name'):
            result['common_name'] = 'Unknown Plant'
        if not result.get('scientific_name'):
            result['scientific_name'] = 'Species unknown'

        try:
            pc = int(float(str(result.get('plant_confidence')).strip().strip('%') or 0))
        except Exception:
            pc = 0
        result['plant_confidence'] = str(max(0, min(100, pc)))

        list_fields = ['disease', 'disease_scientific_name', 'disease_confidence', 'symptoms', 'cause', 'treatment']
        for f in list_fields:
            if f not in result or result[f] is None:
                result[f] = []
            elif not isinstance(result[f], list):
                result[f] = [result[f]]

        cleaned = []
        for v in result.get('disease_confidence', []):
            try:
                iv = int(float(str(v).strip().strip('%')))
            except Exception:
                iv = 0
            iv = max(0, min(100, iv))
            cleaned.append(str(iv))
        if not cleaned and result.get('disease'):
            cleaned = ['0'] * len(result.get('disease'))
        result['disease_confidence'] = cleaned

        try:
            abiotic_list = result.get('_abiotic_issues', []) or []
            if isinstance(abiotic_list, list) and abiotic_list:
                top_abi = 0
                for a in abiotic_list:
                    try:
                        c = int(float(str(a.get('confidence', 0))))
                    except Exception:
                        c = 0
                    top_abi = max(top_abi, c)

                top_dis = 0
                for dc in result.get('disease_confidence', []):
                    try:
                        dci = int(float(str(dc)))
                    except Exception:
                        dci = 0
                    top_dis = max(top_dis, dci)

                if top_abi >= 60 and top_dis < (top_abi + 20):
                    result['disease'] = ["healthy"]
                    result['disease_scientific_name'] = [""]
                    result['disease_confidence'] = ["0"]
        except Exception:
            pass

        api_time = time.time() - start_time
        result['_metadata'] = {
            'selected_image_index': selected_idx,
            'image_type': image_type,
            'optimization': f"{reduction:.1f}% reduction",
            'api_time_seconds': round(api_time, 2)
        }

        print(f"Analysis completed in {api_time:.2f}s")
        return result

    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return {"error": "Invalid JSON response from OpenAI"}
    except Exception as e:
        print(f"Analysis failed: {e}")
        return {"error": f"Analysis failed: {str(e)}"}