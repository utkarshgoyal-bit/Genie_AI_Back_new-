from PIL import Image, ImageFilter
import io

def detect_image_type(image_data: bytes) -> str:
    """
    SMART: Detect if image is close-up or wide-view using edge density.
    Returns: "close_up" or "wide_view"
    """
    try:
        with Image.open(io.BytesIO(image_data)) as img:
            # Quick analysis with small image
            small_img = img.resize((100, 100)).convert('L')
            
            # Calculate edge density (close-ups have more detail)
            edges = small_img.filter(ImageFilter.FIND_EDGES)
            edge_pixels = sum(1 for pixel in edges.getdata() if pixel > 30)
            edge_density = edge_pixels / 10000  # Normalized 0-1
            
            # Classification threshold
            return "close_up" if edge_density > 0.15 else "wide_view"
    except:
        return "unknown"


def optimize_image(image_data: bytes, image_type: str = None) -> bytes:
    """
    SAFE CONDITIONAL OPTIMIZATION:
    - Close-ups: Crop 85% center + resize 512px + compress 75% = 80% reduction
    - Wide-views: Keep full + resize 768px + compress 80% = 60% reduction
    """
    try:
        # Auto-detect type if not provided
        if image_type is None:
            image_type = detect_image_type(image_data)
        
        with Image.open(io.BytesIO(image_data)) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # CONDITIONAL OPTIMIZATION based on image type
            if image_type == "close_up":
                # SAFE to crop - disease in center
                w, h = img.size
                crop_w, crop_h = int(w * 0.85), int(h * 0.85)
                left, top = (w - crop_w) // 2, (h - crop_h) // 2
                img = img.crop((left, top, left + crop_w, top + crop_h))
                max_size = 512
                quality = 75
            else:  # wide_view or unknown
                # Keep full for context
                max_size = 768
                quality = 80
            
            # Resize maintaining aspect ratio
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Compress JPEG
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            return buffer.getvalue()
    except:
        return image_data


def select_best_image(images: list[bytes]) -> tuple[bytes, str, int]:
    """
    SMART: Select best image for disease analysis.
    Returns: (selected_image_bytes, image_type, selected_index)
    """
    if len(images) == 1:
        return images[0], detect_image_type(images[0]), 0
    
    # Detect types for all images
    image_types = [detect_image_type(img) for img in images]
    
    # Prefer close-up for disease analysis
    if "close_up" in image_types:
        idx = image_types.index("close_up")
        return images[idx], "close_up", idx
    
    # No close-up found, use first image
    return images[0], image_types[0], 0