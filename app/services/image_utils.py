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
    LESS AGGRESSIVE OPTIMIZATION (reduced compression & resizing):
    - Close-ups: keep full frame (no center crop), resize to up to 1024px, quality 90
    - Wide-views: resize to up to 1024px, quality 90
    """
    try:
        # Auto-detect type if not provided
        if image_type is None:
            image_type = detect_image_type(image_data)
        
        with Image.open(io.BytesIO(image_data)) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # CONDITIONAL OPTIMIZATION based on image type (less aggressive)
            if image_type == "close_up":
                # Do NOT crop; preserve full frame for analysis
                max_size = 1024
                quality = 90
            else:  # wide_view or unknown
                # Keep full for context, but allow larger resize with higher quality
                max_size = 1024
                quality = 90
            
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