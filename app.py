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
# ⚡ DEDICATED SEO DATABASE FOR ALL 9 TOOLS
# ==========================================
TOOL_SEO = {
    'compress': {
        'slug': 'compress-image',
        'title': 'Compress Image to 20KB, 50KB, 100KB Online Free | SmartPicTools',
        'desc': 'Free online tool to compress image to exact 20KB, 50KB, or any target size with high clarity. Perfect for government exam forms (SSC, UPSC).',
        'keywords': 'compress image to 20kb, compress image to 50kb, compress photo for online exam, exact kb compressor, ssc photo compressor'
    },
    'crop': {
        'slug': 'crop-image',
        'title': 'Crop Image Online Free - Instagram 1:1, YouTube 16:9, Reels | SmartPicTools',
        'desc': 'Crop photos visually with exact aspect ratio presets for Instagram (1:1), YouTube (16:9), and Reels/Shorts (9:16).',
        'keywords': 'crop image online, crop photo 1:1 instagram, crop image 16:9 youtube thumbnail, crop 9:16 reels shorts, aspect ratio cropper'
    },
    'resize': {
        'slug': 'resize-image',
        'title': 'Resize Image Dimensions Online Free - Change Pixel Width & Height | SmartPicTools',
        'desc': 'Resize image dimensions in pixels with live visual transform and aspect ratio lock. Fast, accurate, and private.',
        'keywords': 'resize image online, resize image dimensions, change photo pixel width height, passport size photo resizer, image resolution changer'
    },
    'convert': {
        'slug': 'convert-image',
        'title': 'Convert Image Format Online Free - JPG, PNG, WEBP, AVIF | SmartPicTools',
        'desc': 'Convert single or batch images to JPG, PNG, WEBP, or AVIF with 1-click ZIP download. 100% private in-browser.',
        'keywords': 'convert image format, image converter online, png to jpg, jpg to png, convert image to webp, avif to jpg, batch image converter'
    },
    'pdf': {
        'slug': 'image-to-pdf',
        'title': 'PDF Maker - Merge Images to PDF Online Free (Zero Border) | SmartPicTools',
        'desc': 'Merge multiple JPG, PNG, WEBP, and HEIC photos into one PDF with 0% white borders. Fast 0.5s in-browser generation.',
        'keywords': 'pdf maker, merge pdf, image to pdf, convert jpg to pdf, merge images to pdf, photo to pdf maker, free online pdf merger'
    },
    'heic': {
        'slug': 'heic-to-jpg',
        'title': 'Convert iPhone HEIC to JPG Online Free | SmartPicTools',
        'desc': 'Convert Apple iPhone HEIC and HEIF photos to standard JPG or PNG in 0.5s without uploading to any server.',
        'keywords': 'convert heic to jpg, heic to jpg online, iphone photo to jpg, apple heic converter, heif to jpg, convert heic to png free'
    },
    'watermark': {
        'slug': 'add-watermark',
        'title': 'Add Watermark to Photo Online Free - Grid & Stamp | SmartPicTools',
        'desc': 'Add text watermarks to images online. Protect pictures with diagonal repeated security grids or corner stamps.',
        'keywords': 'add watermark to photo, watermark image online, diagonal grid watermark, copyright photo watermark, free online watermark maker'
    },
    'rotate': {
        'slug': 'rotate-image',
        'title': 'Rotate & Flip Image Online Free - 90 Degree & Mirror | SmartPicTools',
        'desc': 'Rotate images 90 degrees clockwise or anti-clockwise and mirror flip horizontally or vertically in 0.05s.',
        'keywords': 'rotate image online, flip image horizontally, mirror photo online, rotate picture 90 degrees, flip photo vertical'
    },
    'barcode': {
        'slug': 'qr-code-generator',
        'title': 'Free QR Code & Barcode Generator Online with Live Preview | SmartPicTools',
        'desc': 'Generate custom QR codes and standard barcodes online for free with instant live preview. Supports URLs, text, and UPI payments.',
        'keywords': 'free qr code generator, online barcode maker, generate upi qr code, code128 barcode generator, custom qr maker'
    }
}

# ==========================================
# ⚡ DEDICATED TOOL ROUTES
# ==========================================
@app.route('/')
def home():
    return render_template('index.html', active_tool='compress', is_home=True, seo=None)

@app.route('/compress-image')
def compress_route():
    return render_template('index.html', active_tool='compress', is_home=False, seo=TOOL_SEO['compress'])

@app.route('/crop-image')
def crop_route():
    return render_template('index.html', active_tool='crop', is_home=False, seo=TOOL_SEO['crop'])

@app.route('/resize-image')
def resize_route():
    return render_template('index.html', active_tool='resize', is_home=False, seo=TOOL_SEO['resize'])

@app.route('/convert-image')
def convert_route():
    return render_template('index.html', active_tool='convert', is_home=False, seo=TOOL_SEO['convert'])

@app.route('/image-to-pdf')
def pdf_route():
    return render_template('index.html', active_tool='pdf', is_home=False, seo=TOOL_SEO['pdf'])

@app.route('/heic-to-jpg')
def heic_route():
    return render_template('index.html', active_tool='heic', is_home=False, seo=TOOL_SEO['heic'])

@app.route('/add-watermark')
def watermark_route():
    return render_template('index.html', active_tool='watermark', is_home=False, seo=TOOL_SEO['watermark'])

@app.route('/rotate-image')
def rotate_route():
    return render_template('index.html', active_tool='rotate', is_home=False, seo=TOOL_SEO['rotate'])

@app.route('/qr-code-generator')
def qr_route():
    return render_template('index.html', active_tool='barcode', is_home=False, seo=TOOL_SEO['barcode'])

# ⚡ PASSPORT PHOTO MAKER ROUTE
@app.route('/passport-photo-maker')
def passport_photo_page():
    return render_template('passport-photo-maker.html')

# ==========================================
# LEGAL ROUTES
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
# ⚡ MASTER SITEMAP (ALL TOOLS INCLUDED)
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
