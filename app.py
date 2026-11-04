import io
import os
import re
import json
import datetime
from xml.etree import ElementTree as ET
from flask import Flask, render_template, request, send_file, jsonify, Response, redirect
from PIL import Image, ImageDraw

try:
    import pillow_avif
except Exception:
    pass

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    if hasattr(pillow_heif, 'register_avif_opener'):
        pillow_heif.register_avif_opener()
except Exception:
    pass

try:
    import fitz  # PyMuPDF Engine
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
    'pdf': 'PDF', 'doc': 'Word', 'heic': 'HEIC'
}

VALID_CONVERSIONS = {
    'jpg': ['png', 'webp', 'avif', 'svg', 'tiff', 'pdf'],
    'jpeg': ['png', 'webp', 'avif', 'svg', 'tiff', 'pdf'],
    'png': ['jpg', 'webp', 'avif', 'svg', 'tiff', 'pdf'],
    'webp': ['jpg', 'png', 'avif', 'svg', 'tiff', 'pdf'],
    'avif': ['jpg', 'png', 'webp', 'svg', 'tiff', 'pdf'],
    'heic': ['jpg', 'png', 'webp', 'avif', 'svg', 'tiff', 'pdf'],
    'pdf': ['jpg', 'png', 'webp', 'svg', 'tiff', 'doc'],
    'svg': ['jpg', 'png', 'webp', 'pdf', 'tiff'],
    'tiff': ['jpg', 'png', 'webp', 'pdf', 'svg']
}

# ==========================================
# ⚡ HOMEPAGE & HUBS / SPOKES ROUTES
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
    return redirect('/')

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
    return redirect('/')

# ==========================================
# ⚡ STANDALONE ADVANCED UTILITY TOOLS
# ==========================================
@app.route('/compress-image')
def compress_route():
    return render_template('compress-image.html')

@app.route('/passport-photo-maker')
def passport_photo_page():
    return render_template('passport-photo-maker.html')

@app.route('/photo-signature-joiner')
def photo_signature_joiner_page():
    return render_template('photo-signature-joiner.html')

@app.route('/add-name-date-on-photo')
def add_name_date_route():
    return render_template('add-name-date-on-photo.html')

@app.route('/crop-image')
def crop_route():
    return render_template('crop-image.html')

@app.route('/resize-image')
def resize_route():
    return render_template('resize-image.html')

@app.route('/convert-image')
def convert_route():
    return render_template('convert-image.html')

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

@app.route('/crop-pdf')
def crop_pdf_page():
    return render_template('crop-pdf.html')

@app.route('/split-pdf')
def split_pdf_page():
    return render_template('split-pdf.html')
# ⚡ PDF PASSWORD PROTECT & UNLOCK ROUTES
@app.route('/pdf-password')
@app.route('/protect-pdf')
@app.route('/unlock-pdf')
def pdf_password_page():
    return render_template('pdf-password.html')

# ⚡ MILITARY-GRADE AES-256 PDF ENCRYPTION & SMART DECRYPTION ENGINE
@app.route('/api/pdf-password-process', methods=['POST'])
def process_pdf_password():
    try:
        import fitz  # PyMuPDF
        f = request.files.get('file')
        action = request.form.get('action', 'lock')
        password = request.form.get('password', '')

        if not f:
            return jsonify({'error': 'PDF file is required.'}), 400

        raw_name = os.path.splitext(f.filename)[0] or 'document'
        pdf_bytes = f.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        buf = io.BytesIO()

        if action == 'lock':
            if not password:
                doc.close()
                return jsonify({'error': 'Please enter a password to protect the PDF.'}), 400
            # Highest standard AES-256 PDF 2.0 encryption
            doc.save(buf, encryption=fitz.PDF_ENCRYPT_AES_256, user_pw=password, owner_pw=password)
            doc.close()
            buf.seek(0)
            return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name=f"{raw_name}_protected.pdf")
        else:
            # Smart Unlock: First test if it unlocks with empty password (for permission-only locked files)
            if doc.needs_pass:
                rc = doc.authenticate("")
                if rc <= 0:
                    if not password:
                        doc.close()
                        return jsonify({'error': 'This PDF requires a password to open. Please enter the password.'}), 400
                    rc = doc.authenticate(password)
                    if rc <= 0:
                        doc.close()
                        return jsonify({'error': 'Incorrect password! Please verify and enter the correct password.'}), 400
            
            # Save completely unencrypted (permanently removes password & permissions)
            doc.save(buf, encryption=fitz.PDF_ENCRYPT_NONE)
            doc.close()
            buf.seek(0)
            return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name=f"{raw_name}_unlocked.pdf")

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 301 Permanent Redirect to Preserve Google SEO Juice
@app.route('/pdf-converter')
def pdf_converter_alias():
    return redirect('/convert-from-pdf', code=301)

# ==========================================
# ⚡ COREL-DRAW STYLE PDF-TO-SVG CURVES ENGINE
# ==========================================
def generate_unlocked_corel_svg(page):
    raw_svg = page.get_svg_image(text_as_path=True)
    try:
        ET.register_namespace('', 'http://www.w3.org/2000/svg')
        ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
        
        root = ET.fromstring(raw_svg)
        parent_map = {c: p for p in root.iter() for c in p}
        
        glyphs = {}
        for elem in root.iter():
            elem_id = elem.attrib.get('id')
            if elem_id and elem.tag.endswith('path'):
                glyphs[elem_id] = elem.attrib.get('d', '')

        use_nodes = [e for e in root.iter() if e.tag.endswith('use')]
        for use in use_nodes:
            parent = parent_map.get(use)
            if parent is None:
                continue
                
            href = use.attrib.get('{http://www.w3.org/1999/xlink}href') or use.attrib.get('href') or ''
            gid = href.lstrip('#')
            
            if gid in glyphs:
                d_val = glyphs[gid]
                x = use.attrib.get('x', '0')
                y = use.attrib.get('y', '0')
                xf = use.attrib.get('transform', '')
                
                new_p = ET.Element('{http://www.w3.org/2000/svg}path')
                new_p.attrib['d'] = d_val
                
                t_list = []
                if x != '0' or y != '0':
                    t_list.append(f"translate({x},{y})")
                if xf:
                    t_list.append(xf)
                if t_list:
                    new_p.attrib['transform'] = ' '.join(t_list)
                    
                for a in ['fill', 'stroke', 'style']:
                    if a in use.attrib:
                        new_p.attrib[a] = use.attrib[a]
                        
                idx = list(parent).index(use)
                parent.insert(idx, new_p)
                parent.remove(use)
                
        for d in [e for e in root.iter() if e.tag.endswith('defs')]:
            p = parent_map.get(d)
            if p is not None:
                p.remove(d)
                
        for cp in [e for e in root.iter() if e.tag.endswith('clipPath')]:
            p = parent_map.get(cp)
            if p is not None:
                p.remove(cp)
                
        for elem in root.iter():
            if 'clip-path' in elem.attrib:
                del elem.attrib['clip-path']
                
        return ET.tostring(root, encoding='utf-8').decode('utf-8')
    except Exception:
        return raw_svg

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

        if len(uploaded_files) == 1:
            f = uploaded_files[0]
            raw_name = os.path.splitext(f.filename)[0] or 'document'
            doc = fitz.open(stream=f.read(), filetype="pdf")
            
            if len(doc) == 1:
                svg_data = generate_unlocked_corel_svg(doc[0])
                doc.close()
                buf = io.BytesIO(svg_data.encode('utf-8'))
                return send_file(buf, mimetype='image/svg+xml', as_attachment=True, download_name=f"smartpic_{raw_name}.svg")
            else:
                zip_buf = io.BytesIO()
                with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for p in range(len(doc)):
                        svg_data = generate_unlocked_corel_svg(doc[p])
                        zf.writestr(f"{raw_name}_page_{p+1}.svg", svg_data.encode('utf-8'))
                doc.close()
                zip_buf.seek(0)
                return send_file(zip_buf, mimetype='application/zip', as_attachment=True, download_name=f"smartpic_{raw_name}_svg_pack.zip")

        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in uploaded_files:
                raw_name = os.path.splitext(f.filename)[0] or 'document'
                doc = fitz.open(stream=f.read(), filetype="pdf")
                for p in range(len(doc)):
                    svg_data = generate_unlocked_corel_svg(doc[p])
                    zf.writestr(f"{raw_name}_page_{p+1}.svg", svg_data.encode('utf-8'))
                doc.close()

        zip_buf.seek(0)
        return send_file(zip_buf, mimetype='application/zip', as_attachment=True, download_name="smartpic_batch_svg_pack.zip")
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==========================================
# ⚡ 100% GOOGLE-COMPATIBLE ULTRA HD FAVICON (PNG + SVG)
# ==========================================
FAVICON_SVG_DATA = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><defs><linearGradient id='g' x1='0%' y1='0%' x2='100%' y2='100%'><stop offset='0%' stop-color='#6366f1'/><stop offset='50%' stop-color='#a855f7'/><stop offset='100%' stop-color='#ec4899'/></linearGradient></defs><rect width='100' height='100' rx='28' fill='url(#g)'/><path d='M52 16 L24 54 L46 54 L42 84 L76 44 L54 44 Z' fill='#fbbf24'/></svg>"""

def generate_pixel_perfect_favicon(size=96):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw Smooth Purple-to-Pink Gradient
    for y in range(size):
        ratio = y / float(size)
        r = int(99 + (236 - 99) * ratio)
        g = int(102 + (72 - 102) * ratio)
        b = int(241 + (153 - 241) * ratio)
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))
        
    # Mask rounded squircle corners
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    corner_radius = int(size * 0.28)
    mask_draw.rounded_rectangle([0, 0, size, size], radius=corner_radius, fill=255)
    img.putalpha(mask)
    
    # Draw Sharp Golden Thunderbolt
    icon_draw = ImageDraw.Draw(img)
    scale = size / 100.0
    bolt_points = [
        (52 * scale, 16 * scale),
        (24 * scale, 54 * scale),
        (46 * scale, 54 * scale),
        (42 * scale, 84 * scale),
        (76 * scale, 44 * scale),
        (54 * scale, 44 * scale)
    ]
    icon_draw.polygon(bolt_points, fill=(251, 191, 36, 255))
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

@app.route('/favicon.ico')
def serve_favicon_ico():
    buf = generate_pixel_perfect_favicon(96)
    return send_file(buf, mimetype='image/x-icon')

@app.route('/favicon.png')
def serve_favicon_png():
    buf = generate_pixel_perfect_favicon(96)
    return send_file(buf, mimetype='image/png')

@app.route('/favicon.svg')
def serve_favicon_svg():
    return Response(FAVICON_SVG_DATA, mimetype='image/svg+xml')

# ==========================================
# ⚡ SITEMAP & ROBOTS (SEARCH CONSOLE READY)
# ==========================================
@app.route('/sitemap.xml')
def sitemap():
    urls = [
        ('https://smartpictools.in/', '1.0'),
        ('https://smartpictools.in/compress-image', '0.9'),
        ('https://smartpictools.in/passport-photo-maker', '0.9'),
        ('https://smartpictools.in/photo-signature-joiner', '0.9'),
        ('https://smartpictools.in/add-name-date-on-photo', '0.9'),
        ('https://smartpictools.in/crop-image', '0.9'),
        ('https://smartpictools.in/resize-image', '0.9'),
        ('https://smartpictools.in/convert-image', '0.9'),
        ('https://smartpictools.in/crop-pdf', '0.9'),
        ('https://smartpictools.in/split-pdf', '0.9'),
        ('https://smartpictools.in/pdf-password', '0.9'),
        ('https://smartpictools.in/protect-pdf', '0.9'),
        ('https://smartpictools.in/unlock-pdf', '0.9'),
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

# ⚡ GOOGLE ADSENSE AUTHORIZED DIGITAL SELLERS (ADS.TXT)
@app.route('/ads.txt')
def ads_txt():
    # Replace pub-0000000000000000 with your real AdSense Publisher ID upon approval
    ads_content = "google.com, pub-0000000000000000, DIRECT, f08c47fec0942fa0\n"
    return Response(ads_content, mimetype='text/plain')

# ==========================================
# ⚡ LEGAL & COMPANY PAGES
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
# ⚡ FALLBACK AVIF CONVERTER ENGINE
# ==========================================
@app.route('/process', methods=['POST'])
# ⚡ HIGH-SPEED AVIF & FALLBACK ENGINE
@app.route('/process', methods=['POST'])
def process_fallback():
    try:
        file = request.files.get('image')
        target_fmt = request.form.get('format', 'AVIF').upper()
        if not file:
            return jsonify({'error': 'No file provided'}), 400

        img = Image.open(io.BytesIO(file.read()))
        
        # Handle transparency
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            if target_fmt in ['JPG', 'JPEG']:
                bg = Image.new('RGB', img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[3])
                img = bg
        else:
            img = img.convert('RGB')

        # Scale down very large camera photos to ensure sub-second AVIF encoding
        if img.width > 1600 or img.height > 1600:
            img.thumbnail((1600, 1600), Image.Resampling.LANCZOS)

        buf = io.BytesIO()
        out_name = f"smartpic_converted.{target_fmt.lower()}"
        mimetype = f"image/{target_fmt.lower()}"

        if target_fmt == 'AVIF':
            saved = False
            # Method 1: Ultra-fast pillow save with max speed
            try:
                img.save(buf, format='AVIF', quality=65, speed=9)
                saved = True
            except Exception:
                try:
                    img.save(buf, format='AVIF', quality=65)
                    saved = True
                except Exception:
                    pass
            
            # Method 2: Direct pillow-heif encoding
            if not saved:
                import pillow_heif
                heif_file = pillow_heif.from_pillow(img)
                heif_file.save(buf, format="AVIF", quality=65)

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

        buf.seek(0)
        return send_file(buf, mimetype=mimetype, as_attachment=True, download_name=out_name)
    except Exception as e:
        print(f"❌ Process error: {str(e)}")
        return jsonify({'error': str(e)}), 500
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
