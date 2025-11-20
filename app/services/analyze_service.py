from ultralytics import YOLO
import os
import base64
import json
import time
import openai
from pathlib import Path
from dotenv import load_dotenv
from .image_utils import optimize_image, select_best_image, detect_image_type

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# YOLO model
try:
    model = YOLO("app/models/best.pt")
    print("✅ YOLO model loaded successfully")
except Exception as e:
    print(f"❌ Failed to load YOLO model: {e}")
    raise RuntimeError(f"Failed to load YOLO model: {e}")

# OpenAI client
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
    OPTIMIZED: Smart image selection + conditional optimization.
    - Automatically selects best image for disease analysis
    - Applies safe conditional cropping based on image type
    - 70-80% token reduction
    """
    start_time = time.time()
    
    try:
        # SMART: Select best image for analysis (prefer close-up)
        selected_image, image_type, selected_idx = select_best_image(images)
        
        # OPTIMIZED: Apply conditional optimization to selected image
        optimized_image = optimize_image(selected_image, image_type)
        
        # Log optimization info
        original_size = len(selected_image) / 1024
        optimized_size = len(optimized_image) / 1024
        reduction = ((original_size - optimized_size) / original_size) * 100
        print(f"🎯 Image {selected_idx + 1} selected ({image_type}): {original_size:.1f}KB → {optimized_size:.1f}KB ({reduction:.1f}% reduction)")
        
        # Prepare OpenAI request
        content = [{
            "type": "text", 
            "text": "Identify plant species first, then all diseases. JSON: {\"common_name\":\"required\",\"scientific_name\":\"required\",\"plant_confidence\":\"0-100%\",\"disease\":[\"disease names or healthy\"],\"disease_scientific_name\":[\"scientific names\"],\"disease_confidence\":[\"0-100%\"],\"symptoms\":[\"2-3 words max\"],\"cause\":[\"1-2 lines max\"],\"treatment\":[\"1-2 lines max\"]}"
        }]

        # Add optimized image
        b64 = base64.b64encode(optimized_image).decode()
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": content}],
            max_tokens=500,
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        # Ensure plant names never blank
        if not result.get('common_name'):
            result['common_name'] = 'Unknown Plant'
        if not result.get('scientific_name'):
            result['scientific_name'] = 'Species unknown'

        # Ensure arrays for disease fields
        for field in ['disease', 'disease_scientific_name', 'disease_confidence', 'symptoms', 'cause', 'treatment']:
            if field in result and not isinstance(result[field], list):
                result[field] = [result[field]]

        # Calculate API time
        api_time = time.time() - start_time
        
        # Add metadata about image selection and performance
        result['_metadata'] = {
            'selected_image_index': selected_idx,
            'image_type': image_type,
            'optimization': f"{reduction:.1f}% reduction",
            'api_time_seconds': round(api_time, 2)
        }
        
        print(f"✅ Analysis completed in {api_time:.2f}s")
        
        return result

    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return {"error": "Invalid JSON response from OpenAI"}
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return {"error": f"Analysis failed: {str(e)}"}