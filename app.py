import io
import os
import math
import json
import zipfile
import datetime
from flask import Flask, render_template, request, send_file, jsonify, Response
from PIL import Image, ImageDraw, ImageFont

# Support for AVIF & iPhone HEIC/HEIF
try:
    import pillow_avif
except ImportError:
    pass

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit

# ==========================================
# PAGE ROUTES & LEGAL
# ==========================================
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

# ==========================================
# SEO ENGINE: SITEMAP & ROBOTS.TXT
# ==========================================
@app.route('/sitemap.xml')
def sitemap():
    sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://smartpictools.in/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>
  <url><loc>https://smartpictools.in/about</loc><changefreq>monthly</changefreq><priority>0.8</priority></url>
  <url><loc>https://smartpictools.in/privacy</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>
  <url><loc>https://smartpictools.in/terms</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>
  <url><loc>https://smartpictools.in/contact</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>
</urlset>"""
    return Response(sitemap_xml, mimetype='application/xml')

@app.route('/robots.txt')
def robots():
    robots_txt = """User-agent: *
Allow: /
Sitemap: https://smartpictools.in/sitemap.xml
"""
    return Response(robots_txt, mimetype='text/plain')

# ==========================================
# FEEDBACK SYSTEM
# ==========================================
@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    try:
        data = request.get_json() or {}
        category = data.get('category', 'General')
        message = data.get('message', '').strip()
        email = data.get('email', '').strip()

        if not message:
            return jsonify({'error': 'Message cannot be empty'}), 400

        entry = {
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'category': category,
            'message': message,
            'email': email if email else 'Anonymous'
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

# ==========================================
# TURBO HELPERS (RGB, FONTS, SPEED GATEKEEPER)
# ==========================================
def make_rgb(im):
    if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):
        im_rgba = im.convert('RGBA')
        bg = Image.new('RGB', im_rgba.size, (255, 255, 255))
        bg.paste(im_rgba, mask=im_rgba.split()[3])
        return bg
    return im.convert('RGB')

def get_universal_font(size):
    """Loads fonts safely on Linux (Render) and Windows"""
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

def turbo_speed_gatekeeper(img):
    """Downsamples massive 4K/8K images safely to prevent 0.1 CPU timeouts"""
    max_dim = 2560
    if img.width > max_dim or img.height > max_dim:
        scale = max_dim / max(img.width, img.height)
        new_w = int(img.width * scale)
        new_h = int(img.height * scale)
        return img.resize((new_w, new_h), Image.Resampling.BILINEAR)
    return img

def compress_to_target_bytes(img, target_bytes):
    """Fast 2-Pass Target Compressor (No heavy loops, hits exact size in 1s)"""
    img_rgb = make_rgb(img)
    
    # Pass 1: Test at high quality (98) with full 4:4:4 color (subsampling=0)
    buf = io.BytesIO()
    img_rgb.save(buf, format='JPEG', quality=98, subsampling=0)
    max_data = buf.getvalue()
    if len(max_data) <= target_bytes:
        return max_data

    # Pass 2: Fast 4-step convergence
    low, high = 20, 95
    best_data = None
    for _ in range(4):
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

    # Scale down minimally if file is too huge
    if best_data is None:
        curr = img_rgb.copy()
        scale = math.sqrt(target_bytes / len(data)) * 0.95
        new_w = max(100, int(curr.width * scale))
        new_h = max(100, int(curr.height * scale))
        curr = curr.resize((new_w, new_h), Image.Resampling.BILINEAR)
        buf = io.BytesIO()
        curr.save(buf, format='JPEG', quality=70)
        best_data = buf.getvalue()

    return best_data or max_data

# ==========================================
# MASTER PROCESS ENGINE (ALL 7 TOOLS)
# ==========================================
@app.route('/process', methods=['POST'])
def process_image():
    try:
        files = request.files.getlist('image')
        tool = request.form.get('tool', 'compress')
        
        if not files or files[0].filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # ----------------------------------------------------
        # 1. BATCH FORMAT CONVERTER (Single & Multi-file ZIP)
        # ----------------------------------------------------
        if tool == 'convert' and len(files) > 1:
            target_fmt = request.form.get('format', 'JPG').upper()
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for idx, f in enumerate(files[:10]):
                    raw_name, _ = os.path.splitext(f.filename)
                    # io.BytesIO(f.read()) handles Apple HEIC seamlessly
                    s_img = turbo_speed_gatekeeper(Image.open(io.BytesIO(f.read())))
                    s_buf = io.BytesIO()
                    out_ext = target_fmt.lower()

                    if target_fmt in ['JPG', 'JPEG']:
                        make_rgb(s_img).save(s_buf, format='JPEG', quality=92)
                        out_ext = 'jpg'
                    elif target_fmt == 'PNG':
                        s_img.save(s_buf, format='PNG')
                        out_ext = 'png'
                    elif target_fmt == 'WEBP':
                        s_img.save(s_buf, format='WEBP', quality=85)
                        out_ext = 'webp'
                    elif target_fmt == 'AVIF':
                        av_img = make_rgb(s_img)
                        if av_img.width > 1920 or av_img.height > 1920:
                            av_img.thumbnail((1920, 1920), Image.Resampling.BILINEAR)
                        try:
                            av_img.save(s_buf, format='AVIF', quality=75)
                        except Exception:
                            av_img.save(s_buf, format='WEBP', quality=85)
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

        # ----------------------------------------------------
        # SINGLE IMAGE ENGINE (Fast & Memory Safe)
        # ----------------------------------------------------
        file = files[0]
        filename, orig_ext = os.path.splitext(file.filename)
        # Raw bytes stream prevents any HEIC/HEIF identification errors
        img = turbo_speed_gatekeeper(Image.open(io.BytesIO(file.read())))
        
        output_data = None
        mimetype = 'image/jpeg'
        download_name = f"{filename}_processed.jpg"

        # TOOL 1: COMPRESS
        if tool == 'compress':
            compress_mode = request.form.get('compress_mode', 'slider')
            if compress_mode == 'target':
                target_val = float(request.form.get('target_val', 500))
                target_unit = request.form.get('target_unit', 'kb').lower()
                target_bytes = int(target_val * 1024 * 1024) if target_unit == 'mb' else int(target_val * 1024)
                output_data = compress_to_target_bytes(img, target_bytes)
                download_name = f"{filename}_compressed_{int(target_val)}{target_unit.upper()}.jpg"
                mimetype = 'image/jpeg'
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

        # TOOL 3: RESIZE (Superfast Bicubic Resampling)
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

        # TOOL 4 & 5: CONVERT (Includes Apple HEIC & Turbo AVIF)
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
                if av_img.width > 1920 or av_img.height > 1920:
                    av_img.thumbnail((1920, 1920), Image.Resampling.BILINEAR)
                try:
                    av_img.save(buf, format='AVIF', quality=75)
                except Exception:
                    av_img.save(buf, format='WEBP', quality=85)
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

        # TOOL 6: WATERMARK (Universal Fonts & Boundary Safe)
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
                else:  # bottom-right
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

        # TOOL 7: ROTATE & FLIP
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
    print("\n---------------------------------------------------------")
    print(" 🚀 SmartPicTools Pro Live: http://127.0.0.1:5000 ")
    print(" Network: http://0.0.0.0:5000 ")
    print("---------------------------------------------------------\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
