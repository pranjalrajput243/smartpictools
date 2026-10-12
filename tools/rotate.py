import io
from PIL import Image
from tools.common import make_rgb

def process(request, img, filename, orig_ext):
    angle = int(request.form.get('angle', 0))
    flip_mode = request.form.get('flip', 'none')

    if angle % 360 != 0:
        img = img.rotate(-angle, expand=True)

    if flip_mode == 'horizontal':
        img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    elif flip_mode == 'vertical':
        img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

    buf = io.BytesIO()
    if img.mode in ('RGBA', 'LA', 'P'):
        img.save(buf, format='PNG')
        download_name = f"{filename}_modified.png"
        mimetype = 'image/png'
    else:
        make_rgb(img).save(buf, format='JPEG', quality=90)
        download_name = f"{filename}_modified.jpg"
        mimetype = 'image/jpeg'

    return buf.getvalue(), mimetype, download_name