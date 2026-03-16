from PIL import Image
import base64
from io import BytesIO

def convert_image_to_jpeg_base64(image_path, size=(128, 128), quality=85):
    with Image.open(image_path) as im:
        if size:
            im.thumbnail(size, Image.Resampling.LANCZOS)
        buffer = BytesIO()
        im.convert("RGB").save(buffer, format="JPEG", quality=quality)
        base64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return base64_str
