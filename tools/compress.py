import io
import math
from PIL import Image
from tools.common import make_rgb

def compress_to_target_bytes(img, target_bytes):
    img_rgb = make_rgb(img)
    buf = io.BytesIO()
    img_rgb.save(buf, format='JPEG', quality=98, subsampling=0)
    max_data = buf.getvalue()
    if len(max_data) <= target_bytes:
        return max_data

    low, high = 20, 95
    best_data = None
    for _ in range(5):
        mid = (low + high) // 2
        buf = io.BytesIO()
        img_rgb.save(buf, format='JPEG', quality=mid)
        data = buf.getvalue()
        if len(data) <= target_bytes:
            best_data = data
            low = mid + 1
        else:
            high = mid - 1
        if low > high:
            break

    if best_data is None:
        curr_img = img_rgb.copy()
        for _ in range(3):
            scale = math.sqrt(target_bytes / len(data)) * 0.95
            new_w = max(100, int(curr_img.width * scale))
            new_h = max(100, int(curr_img.height * scale))
            curr_img = curr_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            curr_img.save(buf, format='JPEG', quality=65)
            best_data = buf.getvalue()
            if len(best_data) <= target_bytes:
                break
    return best_data or max_data

def process(request, img, filename, orig_ext):
    compress_mode = request.form.get('compress_mode', 'slider')
    if compress_mode == 'target':
        target_val = float(request.form.get('target_val', 500))
        target_unit = request.form.get('target_unit', 'kb').lower()
        target_bytes = int(target_val * 1024 * 1024) if target_unit == 'mb' else int(target_val * 1024)
        output_data = compress_to_target_bytes(img, target_bytes)
        download_name = f"{filename}_compressed_{int(target_val)}{target_unit.upper()}.jpg"
    else:
        quality = int(request.form.get('quality', 65))
        buf = io.BytesIO()
        make_rgb(img).save(buf, format='JPEG', optimize=True, quality=quality)
        output_data = buf.getvalue()
        download_name = f"{filename}_compressed.jpg"

    return output_data, 'image/jpeg', download_name