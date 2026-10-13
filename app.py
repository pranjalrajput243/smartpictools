import io
import os
import math
import json
import zipfile
import datetime
from flask import Flask, render_template, request, send_file, jsonify, Response
from PIL import Image, ImageDraw, ImageFont

# ⚡ Bulletproof AVIF & iPhone HEIC/HEIF Engine
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    pillow_heif.register_avif_opener()
except Exception as e:
    print("HEIF/AVIF init error:", e)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/sitemap.xml')
def sitemap():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://smartpictools.in/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>
  <url><loc>https://smartpictools.in/about</loc><changefreq>monthly</changefreq><priority>0.8</priority></url>
  <url><loc>https://smartpictools.in/privacy</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>
  <url><loc>https://smartpictools.in/terms</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>
  <url><loc>https://smartpictools.in/contact</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>
</urlset>"""
    return Response(xml, mimetype='application/xml')

@app.route('/robots.txt')
def robots():
    txt = "User-agent: *\nAllow: /\nSitemap: https://smartpictools.in/sitemap.xml\n"
    return Response(txt, mimetype='text/plain')

@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    try:
        data = request.get_json() or {}
        entry = {
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'category': data.get('category', 'General'),
            'message': data.get('message', '').strip(),
            'email': data.get('email', 'Anonymous')
        }
        feedbacks = []
        if os.path.exists('feedback.json'):
            try:
                with open('feedback.json', 'r', encoding='utf-8') as f:
                    feedbacks = json.load(f)
            except Exception:
                feedbacks = []
        feedbacks.append(entry)
        with open('feedback.json', 'w', encoding='utf-8') as f:
            json.dump(feedbacks, f, indent=4)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

def turbo_speed_gatekeeper(img):
    max_dim = 2560
    if img.width > max_dim or img.height > max_dim:
        scale = max_dim / max(img.width, img.height)
        new_w = max(100, int(img.width * scale))
        new_h = max(100, int(img.height * scale))
        return img.resize((new_w, new_h), Image.Resampling.BILINEAR)
    return img

def fast_direct_compress(img, original_size_bytes, target_bytes):
    img_rgb = make_rgb(img)
    ratio = target_bytes / max(1, original_size_bytes)

    if ratio <= 0.15:
        scale = math.sqrt(ratio * 2.2)
        new_w = max(400, int(img_rgb.width * scale))
        new_h = max(400, int(img_rgb.height * scale))
        img_rgb = img_rgb.resize((new_w, new_h), Image.Resampling.BILINEAR)
        quality = 38
    elif ratio <= 0.35:
        quality = 52
    elif ratio <= 0.60:
        quality = 68
    elif ratio <= 0.85:
        quality = 80
    else:
        quality = 92

    buf = io.BytesIO()
    img_rgb.save(buf, format='JPEG', quality=quality)
    return buf.getvalue()

@app.route('/process', methods=['POST'])
def process_image():
    try:
        files = request.files.getlist('image')
        tool = request.form.get('tool', 'compress')
        
        if not files or files[0].filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # BATCH CONVERTER (ZIP)
        if tool == 'convert' and len(files) > 1:
            target_fmt = request.form.get('format', 'JPG').upper()
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for idx, f in enumerate(files[:10]):
                    raw_name, _ = os.path.splitext(f.filename)
                    s_img = turbo_speed_gatekeeper(Image.open(io.BytesIO(f.read())))
                    s_buf = io.BytesIO()
                    out_ext = target_fmt.lower()

                    if target_fmt in ['JPG', 'JPEG']:
                        make_rgb(s_img).save(s_buf, format='JPEG', quality=90)
                        out_ext = 'jpg'
                    elif target_fmt == 'PNG':
                        s_img.save(s_buf, format='PNG')
                        out_ext = 'png'
                    elif target_fmt == 'WEBP':
                        s_img.save(s_buf, format='WEBP', quality=85)
                        out_ext = 'webp'
                    elif target_fmt == 'AVIF':
                        av = make_rgb(s_img)
                        av.save(s_buf, format='AVIF', quality=75)
                        out_ext = 'avif'
                    elif target_fmt == 'PDF':
                        make_rgb(s_img).save(s_buf, format='PDF')
                        out_ext = 'pdf'
                    elif target_fmt == 'BMP':
                        make_rgb(s_img).save(s_buf, format='BMP')
                        out_ext = 'bmp'
                    elif target_fmt == 'ICO':
                        make_rgb(s_img).resize((64, 64), Image.Resampling.BILINEAR).save(s_buf, format='ICO')
                        out_ext = 'ico'

                    zip_file.writestr(f"{raw_name}_converted.{out_ext}", s_buf.getvalue())
            
            return send_file(
                io.BytesIO(zip_buffer.getvalue()),
                mimetype='application/zip',
                as_attachment=True,
                download_name='smartpic_converted_batch.zip'
            )

        # SINGLE IMAGE ENGINE
        file = files[0]
        filename, orig_ext = os.path.splitext(file.filename)
        raw_bytes = file.read()
        original_size_bytes = len(raw_bytes)
        
        img = turbo_speed_gatekeeper(Image.open(io.BytesIO(raw_bytes)))
        
        output_data = None
        mimetype = 'image/jpeg'
        download_name = f"{filename}_processed.jpg"

        # TOOL 1: COMPRESS
        if tool == 'compress':
            compress_mode = request.form.get('compress_mode', 'target')
            if compress_mode == 'target':
                target_val = float(request.form.get('target_val', 500))
                target_unit = request.form.get('target_unit', 'kb').lower()
                target_bytes = int(target_val * 1024 * 1024) if target_unit == 'mb' else int(target_val * 1024)
                output_data = fast_direct_compress(img, original_size_bytes, target_bytes)
                download_name = f"{filename}_compressed_{int(target_val)}{target_unit.upper()}.jpg"
            else:
                quality = int(request.form.get('quality', 65))
                buf = io.BytesIO()
                make_rgb(img).save(buf, format='JPEG', quality=quality)
                output_data = buf.getvalue()
                download_name = f"{filename}_compressed.jpg"
            mimetype = 'image/jpeg'

        # TOOL 2: CROP
        elif tool == 'crop':
            x = max(0, int(float(request.form.get('crop_x', 0))))
            y = max(0, int(float(request.form.get('crop_y', 0))))
            w = int(float(request.form.get('crop_w', img.width)))
            h = int(float(request.form.get('crop_h', img.height)))
            img = img.crop((x, y, x + w, y + h))
            
            buf = io.BytesIO()
            if img.mode in ('RGBA', 'LA', 'P'):
                img.save(buf, format='PNG')
                download_name = f"{filename}_cropped.png"
                mimetype = 'image/png'
            else:
                make_rgb(img).save(buf, format='JPEG', quality=95)
                download_name = f"{filename}_cropped.jpg"
                mimetype = 'image/jpeg'
            output_data = buf.getvalue()

        # TOOL 3: RESIZE
        elif tool == 'resize':
            width = int(request.form.get('width', img.width))
            height = int(request.form.get('height', img.height))
            img = img.resize((width, height), Image.Resampling.BICUBIC)
            
            buf = io.BytesIO()
            if img.mode in ('RGBA', 'LA', 'P'):
                img.save(buf, format='PNG')
                download_name = f"{filename}_resized.png"
                mimetype = 'image/png'
            else:
                make_rgb(img).save(buf, format='JPEG', quality=92)
                download_name = f"{filename}_resized.jpg"
                mimetype = 'image/jpeg'
            output_data = buf.getvalue()

        # TOOL 4: CONVERT
        elif tool == 'convert':
            target_fmt = request.form.get('format', 'JPG').upper()
            buf = io.BytesIO()
            
            if target_fmt == 'PDF':
                make_rgb(img).save(buf, format='PDF')
                download_name = f"{filename}_converted.pdf"
                mimetype = 'application/pdf'
            elif target_fmt in ['JPG', 'JPEG']:
                make_rgb(img).save(buf, format='JPEG', quality=95)
                download_name = f"{filename}_converted.jpg"
                mimetype = 'image/jpeg'
            elif target_fmt == 'PNG':
                img.save(buf, format='PNG')
                download_name = f"{filename}_converted.png"
                mimetype = 'image/png'
            elif target_fmt == 'WEBP':
                img.save(buf, format='WEBP', quality=90)
                download_name = f"{filename}_converted.webp"
                mimetype = 'image/webp'
            elif target_fmt == 'AVIF':
                av_img = make_rgb(img)
                av_img.save(buf, format='AVIF', quality=75)
                download_name = f"{filename}_converted.avif"
                mimetype = 'image/avif'
            elif target_fmt == 'BMP':
                make_rgb(img).save(buf, format='BMP')
                download_name = f"{filename}_converted.bmp"
                mimetype = 'image/bmp'
            elif target_fmt == 'ICO':
                make_rgb(img).resize((64, 64), Image.Resampling.BILINEAR).save(buf, format='ICO')
                download_name = f"{filename}_converted.ico"
                mimetype = 'image/x-icon'
            output_data = buf.getvalue()

        # TOOL 5: WATERMARK
        elif tool == 'watermark':
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
            output_data = buf.getvalue()

        # TOOL 6: ROTATE & FLIP
        elif tool == 'rotate':
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
            output_data = buf.getvalue()

        return send_file(
            io.BytesIO(output_data),
            mimetype=mimetype,
            as_attachment=True,
            download_name=download_name
        )

    except Exception as e:
        print("Backend Error:", str(e))
        return jsonify({'error': f"Processing failed: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
