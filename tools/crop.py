import io
from PIL import Image
from tools.common import make_rgb

def process(request, img, filename, orig_ext):
    x = max(0, int(float(request.form.get('crop_x', 0))))
    y = max(0, int(float(request.form.get('crop_y', 0))))
    w = int(float(request.form.get('crop_w', img.width)))
    h = int(float(request.form.get('crop_h', img.height)))
    img_cropped = img.crop((x, y, x + w, y + h))
    
    buf = io.BytesIO()
    if img_cropped.mode in ('RGBA', 'LA', 'P'):
        img_cropped.save(buf, format='PNG')
        download_name = f"{filename}_cropped.png"
        mimetype = 'image/png'
    else:
        make_rgb(img_cropped).save(buf, format='JPEG', quality=95)
        download_name = f"{filename}_cropped.jpg"
        mimetype = 'image/jpeg'

    return buf.getvalue(), mimetype, download_name