import io
from PIL import Image, ImageDraw
from tools.common import make_rgb, get_universal_font

def process(request, img, filename, orig_ext):
    text = request.form.get('watermark_text', '© SmartPicTools')
    mode = request.form.get('watermark_mode', 'single')
    pos = request.form.get('watermark_pos', 'bottom-right')
    color_choice = request.form.get('watermark_color', 'white')
    size_choice = int(request.form.get('watermark_size', 36))
    opacity = int(request.form.get('watermark_opacity', 160))

    img_rgba = img.convert('RGBA')
    txt_layer = Image.new('RGBA', img_rgba.size, (255, 255, 255, 0))
    font = get_universal_font(size_choice)

    color_map = {
        'white': (255, 255, 255),
        'black': (0, 0, 0),
        'gold': (251, 191, 36),
        'red': (239, 68, 68),
        'cyan': (6, 182, 212)
    }
    base_rgb = color_map.get(color_choice, (255, 255, 255))
    fill_color = (*base_rgb, opacity)

    if mode == 'repeat':
        draw_tmp = ImageDraw.Draw(txt_layer)
        bbox = draw_tmp.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        stamp = Image.new('RGBA', (tw + 90, th + 55), (255, 255, 255, 0))
        draw_stamp = ImageDraw.Draw(stamp)
        draw_stamp.text((45, 25), text, font=font, fill=fill_color)
        rotated_stamp = stamp.rotate(30, expand=True, resample=Image.Resampling.BICUBIC)

        rw, rh = rotated_stamp.size
        for x in range(-rw // 2, img.width + rw, rw + 40):
            for y in range(-rh // 2, img.height + rh, rh + 40):
                txt_layer.paste(rotated_stamp, (x, y), rotated_stamp)
    else:
        draw = ImageDraw.Draw(txt_layer)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        margin = int(img.width * 0.03)

        if pos == 'center':
            x = (img.width - tw) // 2
            y = (img.height - th) // 2
        elif pos == 'top-left':
            x, y = margin, margin
        elif pos == 'top-right':
            x, y = img.width - tw - margin, margin
        elif pos == 'bottom-left':
            x, y = margin, img.height - th - margin
        else:
            x, y = img.width - tw - margin, img.height - th - margin

        draw.text((x, y), text, font=font, fill=fill_color)

    combined = Image.alpha_composite(img_rgba, txt_layer)

    buf = io.BytesIO()
    if orig_ext.lower() in ['.png', '.webp']:
        combined.save(buf, format='PNG')
        download_name = f"{filename}_watermarked.png"
        mimetype = 'image/png'
    else:
        make_rgb(combined).save(buf, format='JPEG', quality=95)
        download_name = f"{filename}_watermarked.jpg"
        mimetype = 'image/jpeg'

    return buf.getvalue(), mimetype, download_name