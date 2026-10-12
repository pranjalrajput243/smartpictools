import io
from PIL import Image, ImageFont

def make_rgb(im):
    if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):
        im_rgba = im.convert('RGBA')
        bg = Image.new('RGB', im_rgba.size, (255, 255, 255))
        bg.paste(im_rgba, mask=im_rgba.split()[3])
        return bg
    return im.convert('RGB')

def get_universal_font(size):
    font_candidates = [
        "DejaVuSans-Bold.ttf", "DejaVuSans.ttf",
        "FreeSansBold.ttf", "FreeSans.ttf",
        "LiberationSans-Bold.ttf", "LiberationSans-Regular.ttf",
        "arial.ttf"
    ]
    for fn in font_candidates:
        try:
            return ImageFont.truetype(fn, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()