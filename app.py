import io
import os
import json
import datetime
from flask import Flask, render_template, request, send_file, jsonify, Response
from PIL import Image

try:
    import pillow_avif
except Exception:
    pass

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except Exception:
    pass

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit

# ==========================================
# ⚡ ALL DEDICATED TOOL ROUTES
# ==========================================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/compress-image')
def compress_route():
    return render_template('compress-image.html')

@app.route('/crop-image')
def crop_route():
    return render_template('crop-image.html')

@app.route('/resize-image')
def resize_route():
    return render_template('resize-image.html')

@app.route('/convert-image')
def convert_route():
    return render_template('convert-image.html')

@app.route('/image-to-pdf')
def pdf_route():
    return render_template('image-to-pdf.html')

@app.route('/heic-to-jpg')
def heic_route():
    return render_template('heic-to-jpg.html')

@app.route('/add-watermark')
def watermark_route():
    return render_template('add-watermark.html')

@app.route('/rotate-image')
def rotate_route():
    return render_template('rotate-image.html')

@app.route('/qr-code-generator')
def qr_route():
    return render_template('qr-code-generator.html')

# ⚡ PASSPORT PHOTO MAKER ROUTE
@app.route('/passport-photo-maker')
def passport_photo_page():
    return render_template('passport-photo-maker.html')

# ⚡ PDF CONVERTER ROUTE
@app.route('/pdf-converter')
def pdf_converter_page():
    return render_template('pdf-converter.html')

# ⚡ FAVICON CONVERTER ROUTE
@app.route('/favicon-converter')
def favicon_converter_page():
    return render_template('favicon-converter.html')
    
# ==========================================
# LEGAL & INFO ROUTES
# ==========================================
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
# ⚡ MASTER SITEMAP (ALL 15 URLS INCLUDED)
# ==========================================
@app.route('/sitemap.xml')
def sitemap():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://smartpictools.in/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>
  <url><loc>https://smartpictools.in/compress-image</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>
  <url><loc>https://smartpictools.in/image-to-pdf</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>
  <url><loc>https://smartpictools.in/crop-image</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>
  <url><loc>https://smartpictools.in/resize-image</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>
  <url><loc>https://smartpictools.in/convert-image</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>
  <url><loc>https://smartpictools.in/heic-to-jpg</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>
  <url><loc>https://smartpictools.in/add-watermark</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>
  <url><loc>https://smartpictools.in/rotate-image</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>
  <url><loc>https://smartpictools.in/qr-code-generator</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>
  <url><loc>https://smartpictools.in/passport-photo-maker</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>
  <url><loc>https://smartpictools.in/about</loc><changefreq>monthly</changefreq><priority>0.8</priority></url>
  <url><loc>https://smartpictools.in/privacy</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>
  <url><loc>https://smartpictools.in/terms</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>
  <url><loc>https://smartpictools.in/contact</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>
  <url><loc>https://smartpictools.in/pdf-converter</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>
  <url><loc>https://smartpictools.in/favicon-converter</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>
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

# ⚡ TURBO AVIF FALLBACK ENGINE
@app.route('/process', methods=['POST'])
def process_fallback():
    try:
        file = request.files.get('image')
        target_fmt = request.form.get('format', 'AVIF').upper()
        if not file:
            return jsonify({'error': 'No file provided'}), 400

        img = Image.open(io.BytesIO(file.read()))
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            if target_fmt in ['JPG', 'JPEG']:
                bg = Image.new('RGB', img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[3])
                img = bg
        else:
            img = img.convert('RGB')

        if img.width > 1280 or img.height > 1280:
            img.thumbnail((1280, 1280), Image.Resampling.BILINEAR)

        buf = io.BytesIO()
        out_name = f"smartpic_converted.{target_fmt.lower()}"
        mimetype = f"image/{target_fmt.lower()}"

        if target_fmt == 'AVIF':
            try:
                img.save(buf, format='AVIF', quality=60, speed=10)
            except Exception:
                img.save(buf, format='AVIF', quality=60)
        elif target_fmt in ['JPG', 'JPEG']:
            img.save(buf, format='JPEG', quality=90)
            mimetype = 'image/jpeg'
        elif target_fmt == 'PNG':
            img.save(buf, format='PNG')
        elif target_fmt == 'WEBP':
            img.save(buf, format='WEBP', quality=85)

        return send_file(io.BytesIO(buf.getvalue()), mimetype=mimetype, as_attachment=True, download_name=out_name)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
