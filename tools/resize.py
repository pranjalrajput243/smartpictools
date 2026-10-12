import io
from PIL import Image
from tools.common import make_rgb

def process(request, img, filename, orig_ext):
    width = int(request.form.get('width', img.width))
    height = int(request.form.get('height', img.height))
    img_resized = img.resize((width, height), Image.Resampling.LANCZOS)
    
    buf = io.BytesIO()
    if img_resized.mode in ('RGBA', 'LA', 'P'):
        img_resized.save(buf, format='PNG')
        download_name = f"{filename}_resized.png"
        mimetype = 'image/png'
    else:
        make_rgb(img_resized).save(buf, format='JPEG', quality=90)
        download_name = f"{filename}_resized.jpg"
        mimetype = 'image/jpeg'

    return buf.getvalue(), mimetype, download_name