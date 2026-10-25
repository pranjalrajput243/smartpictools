import io
import os
import re
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

try:
    import fitz  # ⚡ PyMuPDF Engine (For CorelDraw-style Convert to Curves)
except Exception:
    pass

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit

# ==========================================
# ⚡ COMPLETE SUPPORTED FORMATS DATABASE
# ==========================================
FORMAT_NAMES = {
    'jpg': 'JPG', 'jpeg': 'JPG', 'png': 'PNG', 'webp': 'WEBP',
    'avif': 'AVIF', 'svg': 'SVG', 'tiff': 'TIFF', 'tif': 'TIFF',
    'pdf': 'PDF', 'doc': 'Word'
}

VALID_CONVERSIONS = {
    'jpg': ['png', 'webp', 'avif', 'svg', 'tiff', 'pdf'],
    'jpeg': ['png', 'webp', 'avif', 'svg', 'tiff', 'pdf'],
    'png': ['jpg', 'webp', 'avif', 'svg', 'tiff', 'pdf'],
    'webp': ['jpg', 'png', 'avif', 'svg', 'tiff', 'pdf'],
    'heic': ['jpg', 'png', 'webp', 'avif', 'svg', 'tiff', 'pdf'],
    'pdf': ['jpg', 'png', 'webp', 'svg', 'tiff', 'doc'],
    'svg': ['jpg', 'png', 'webp', 'pdf', 'tiff'],
    'tiff': ['jpg', 'png', 'webp', 'pdf', 'svg']
}

# ==========================================
# ⚡ UNIVERSAL DYNAMIC HUBS & SPOKES
# ==========================================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/convert-from-<src>')
def universal_hub(src):
    src = src.lower()
    if src in VALID_CONVERSIONS:
        src_name = FORMAT_NAMES.get(src, src.upper())
        targets = [{
            'slug': f"{src}-to-{t}",
            'target': t,
            'target_name': FORMAT_NAMES.get(t, t.upper())
        } for t in VALID_CONVERSIONS[src]]
        return render_template('format-hub.html', src=src, src_name=src_name, targets=targets)
    return render_template('index.html')

@app.route('/<src>-to-<tgt>')
def universal_conversion_tool(src, tgt):
    src = src.lower()
    tgt = tgt.lower()
    if src in VALID_CONVERSIONS and tgt in VALID_CONVERSIONS[src]:
        src_name = FORMAT_NAMES.get(src, src.upper())
        tgt_name = FORMAT_NAMES.get(tgt, tgt.upper())
        meta = {
            'src': src,
            'tgt': tgt,
            'src_name': src_name,
            'tgt_name': tgt_name,
            'title': f"Convert {src_name} to {tgt_name} Online Free - High Quality | SmartPicTools",
            'desc': f"Free online tool to convert {src_name} into {tgt_name} in 0.1s. 100% private in-browser conversion with zero server uploads.",
            'keywords': f"convert {src} to {tgt}, {src} to {tgt} converter, {src} to {tgt} online free, batch {src} to {tgt}"
        }
        return render_template('universal-converter.html', meta=meta)
    return render_template('index.html')

# ==========================================
# ⚡ STANDALONE ADVANCED TOOLS
# ==========================================
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

@app.route('/passport-photo-maker')
def passport_photo_page():
    return render_template('passport-photo-maker.html')

@app.route('/add-watermark')
def watermark_route():
    return render_template('add-watermark.html')

@app.route('/rotate-image')
def rotate_route():
    return render_template('rotate-image.html')

@app.route('/qr-code-generator')
def qr_route():
    return render_template('qr-code-generator.html')

@app.route('/favicon-converter')
def favicon_converter_page():
    return render_template('favicon-converter.html')

@app.route('/image-to-pdf')
def image_to_pdf_alias():
    return render_template('image-to-pdf.html')

@app.route('/pdf-converter')
def pdf_converter_alias():
    return render_template('pdf-converter.html')

@app.route('/crop-pdf')
def crop_pdf_page():
    return render_template('crop-pdf.html')

# ==========================================
# ⚡ CORELDRAW STYLE PDF-TO-SVG (UNLOCKED VECTOR CURVES)
# ==========================================
@app.route('/convert-pdf-to-svg-curves', methods=['POST'])
def convert_pdf_to_svg_curves():
    try:
        import fitz
        import zipfile
        
        uploaded_files = request.files.getlist('files')
        if not uploaded_files or not uploaded_files[0].filename:
            f = request.files.get('file')
            uploaded_files = [f] if f else []

        if not uploaded_files:
            return jsonify({'error': 'No PDF file provided'}), 400

        def get_clean_unlocked_svg(page):
            # 1. Convert text to vector curve paths
            svg = page.get_svg_image(text_as_path=True)
            # 2. ⚡ Strip clip-paths so CorelDraw never locks objects!
            svg = re.sub(r'\s+clip-path="url\(#[^"]+\)"', '', svg)
            svg = re.sub(r'<clipPath[^>]*>.*?</clipPath>', '', svg, flags=re.DOTALL)
            return svg

        # Case A: 1 PDF file
        if len(uploaded_files) == 1:
            f = uploaded_files[0]
            raw_name = os.path.splitext(f.filename)[0] or 'document'
            pdf_bytes = f.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            # Single Page PDF -> Download as .SVG directly
            if len(doc) == 1:
                svg_data = get_clean_unlocked_svg(doc[0])
                doc.close()
                buf = io.BytesIO(svg_data.encode('utf-8'))
                return send_file(
                    buf,
                    mimetype='image/svg+xml',
                    as_attachment=True,
                    download_name=f"smartpic_{raw_name}_curves.svg"
                )
            else:
                # Multi-page PDF -> Download as ZIP containing .SVG of each page
                zip_buf = io.BytesIO()
                with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for p in range(len(doc)):
                        svg_data = get_clean_unlocked_svg(doc[p])
                        zf.writestr(f"{raw_name}_page_{p+1}_curves.svg", svg_data.encode('utf-8'))
                doc.close()
                zip_buf.seek(0)
                return send_file(
                    zip_buf,
                    mimetype='application/zip',
                    as_attachment=True,
                    download_name=f"smartpic_{raw_name}_svg_pack.zip"
                )

        # Case B: Multiple PDF files uploaded
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in uploaded_files:
                raw_name = os.path.splitext(f.filename)[0] or 'document'
                pdf_bytes = f.read()
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                for p in range(len(doc)):
                    svg_data = get_clean_unlocked_svg(doc[p])
                    zf.writestr(f"{raw_name}_page_{p+1}_curves.svg", svg_data.encode('utf-8'))
                doc.close()

        zip_buf.seek(0)
        return send_file(
            zip_buf,
            mimetype='application/zip',
            as_attachment=True,
            download_name="smartpic_batch_svg_pack.zip"
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==========================================
# LEGAL & INFO
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

# FAVICON
FAVICON_SVG_DATA = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><defs><linearGradient id='g' x1='0%' y1='0%' x2='100%' y2='100%'><stop offset='0%' stop-color='%236366f1'/><stop offset='50%' stop-color='%23a855f7'/><stop offset='100%' stop-color='%23ec4899'/></linearGradient></defs><rect width='100' height='100' rx='28' fill='url(#g)'/><path d='M52 16 L24 54 L46 54 L42 84 L76 44 L54 44 Z' fill='#fbbf24'/></svg>"""

@app.route('/favicon.ico')
@app.route('/favicon.svg')
def serve_favicon():
    return Response(FAVICON_SVG_DATA, mimetype='image/svg+xml')

# SITEMAP & ROBOTS
@app.route('/sitemap.xml')
def sitemap():
    urls = [
        ('https://smartpictools.in/', '1.0'),
        ('https://smartpictools.in/compress-image', '0.9'),
        ('https://smartpictools.in/passport-photo-maker', '0.9'),
        ('https://smartpictools.in/crop-image', '0.9'),
        ('https://smartpictools.in/resize-image', '0.9'),
        ('https://smartpictools.in/convert-image', '0.9'),
        ('https://smartpictools.in/crop-pdf', '0.9'),
        ('https://smartpictools.in/add-watermark', '0.9'),
        ('https://smartpictools.in/rotate-image', '0.9'),
        ('https://smartpictools.in/qr-code-generator', '0.9'),
        ('https://smartpictools.in/favicon-converter', '0.9'),
        ('https://smartpictools.in/about', '0.8'),
        ('https://smartpictools.in/privacy', '0.5'),
        ('https://smartpictools.in/terms', '0.5'),
        ('https://smartpictools.in/contact', '0.6'),
    ]

    for src, tgts in VALID_CONVERSIONS.items():
        urls.append((f"https://smartpictools.in/convert-from-{src}", '0.9'))
        for t in tgts:
            urls.append((f"https://smartpictools.in/{src}-to-{t}", '0.8'))

    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u, p in urls:
        xml.append(f'  <url><loc>{u}</loc><changefreq>weekly</changefreq><priority>{p}</priority></url>')
    xml.append('</urlset>')

    return Response("\n".join(xml), mimetype='application/xml')

@app.route('/robots.txt')
def robots():
    txt = "User-agent: *\nAllow: /\nSitemap: https://smartpictools.in/sitemap.xml\n"
    return Response(txt, mimetype='text/plain')

# TURBO AVIF FALLBACK ENGINE
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
        elif target_fmt in ['TIFF', 'TIF']:
            img.save(buf, format='TIFF')
            mimetype = 'image/tiff'

        return send_file(io.BytesIO(buf.getvalue()), mimetype=mimetype, as_attachment=True, download_name=out_name)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
