import io
import os
import zipfile
from PIL import Image
from tools.common import make_rgb

def convert_single_image(img, target_fmt, filename):
    buf = io.BytesIO()
    if target_fmt == 'PDF':
        make_rgb(img).save(buf, format='PDF')
        download_name = f"{filename}_converted.pdf"
        mimetype = 'application/pdf'
    elif target_fmt in ['JPG', 'JPEG']:
        make_rgb(img).save(buf, format='JPEG', quality=95, optimize=True)
        download_name = f"{filename}_converted.jpg"
        mimetype = 'image/jpeg'
    elif target_fmt == 'PNG':
        img.save(buf, format='PNG', optimize=True)
        download_name = f"{filename}_converted.png"
        mimetype = 'image/png'
    elif target_fmt == 'WEBP':
        img.save(buf, format='WEBP', quality=90)
        download_name = f"{filename}_converted.webp"
        mimetype = 'image/webp'
    elif target_fmt == 'AVIF':
        avif_img = make_rgb(img)
        if avif_img.width > 1920 or avif_img.height > 1920:
            avif_img.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
        try:
            avif_img.save(buf, format='AVIF', quality=75)
        except Exception:
            avif_img.save(buf, format='WEBP', quality=85)
        download_name = f"{filename}_converted.avif"
        mimetype = 'image/avif'
    elif target_fmt == 'BMP':
        make_rgb(img).save(buf, format='BMP')
        download_name = f"{filename}_converted.bmp"
        mimetype = 'image/bmp'
    elif target_fmt == 'ICO':
        make_rgb(img).resize((64, 64), Image.Resampling.LANCZOS).save(buf, format='ICO')
        download_name = f"{filename}_converted.ico"
        mimetype = 'image/x-icon'

    return buf.getvalue(), mimetype, download_name

def process(request, img, filename, orig_ext, files=None):
    target_fmt = request.form.get('format', 'JPG').upper()
    
    # Batch convert ZIP
    if files and len(files) > 1:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for f in files[:10]:
                raw_name, _ = os.path.splitext(f.filename)
                single_img = Image.open(io.BytesIO(f.read()))
                data, _, dl_name = convert_single_image(single_img, target_fmt, raw_name)
                zip_file.writestr(dl_name, data)
        return zip_buffer.getvalue(), 'application/zip', 'smartpic_converted_batch.zip'

    return convert_single_image(img, target_fmt, filename)