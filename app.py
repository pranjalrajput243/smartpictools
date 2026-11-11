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

@app.route('/compress-image-to-<int:target_kb>kb')
def compress_exact_kb_route(target_kb):
    if target_kb in [20, 50, 100, 200]:
        use_case = "Signature & Thumb Impression" if target_kb == 20 else ("Official SSC/UPSC Photo" if target_kb == 50 else "Online Application Forms")
        meta = {
            'target_kb': target_kb,
            'title': f"Compress Image to {target_kb}KB Online Free - Exact Size for {use_case} | SmartPicTools",
            'desc': f"Compress image to exact {target_kb}KB online free with live preview. Perfect for {use_case}. 100% private in-browser tool with zero server uploads.",
            'canonical': f"https://smartpictools.in/compress-image-to-{target_kb}kb"
        }
        return render_template('compress-image.html', meta=meta)
    return redirect('/compress-image')

@app.route('/passport-photo-maker')
def passport_photo_page():
    return render_template('passport-photo-maker.html')

# ⚡ DEDICATED HIGH-INTENT PASSPORT SPOKES
@app.route('/passport-photo-3.5x4.5-cm')
@app.route('/2x2-inch-visa-photo-maker')
@app.route('/passport-photo-4x6-sheet')
def passport_spokes_route():
    endpoint = request.path.strip('/')
    spokes = {
        'passport-photo-3.5x4.5-cm': {
            'size_preset': '3.5x4.5',
            'sheet_type': 'single',
            'title': 'Passport Photo 3.5 x 4.5 cm Maker Online Free - SSC, UPSC 300 DPI | SmartPicTools',
            'desc': 'Create official 3.5 x 4.5 cm passport size photos online for SSC, UPSC, and Indian exam forms. 300 DPI Ultra HD, 100% private in-browser.',
            'h1': 'Passport Photo 3.5 × 4.5 cm Maker',
            'canonical': 'https://smartpictools.in/passport-photo-3.5x4.5-cm'
        },
        '2x2-inch-visa-photo-maker': {
            'size_preset': '2x2',
            'sheet_type': 'single',
            'title': '2x2 Inch Visa Photo Maker Online Free - US, Schengen & OCI (51x51mm) | SmartPicTools',
            'desc': 'Free online 2x2 inch (51x51 mm) photo creator for US Visa, Schengen, OCI, and international passports in 300 DPI studio quality.',
            'h1': '2 × 2 Inch Visa Photo Maker',
            'canonical': 'https://smartpictools.in/2x2-inch-visa-photo-maker'
        },
        'passport-photo-4x6-sheet': {
            'size_preset': '3.5x4.5',
            'sheet_type': '4x6',
            'title': 'Create Passport Size Photo 4x6 Printable Sheet Online Free | SmartPicTools',
            'desc': 'Generate printable 4x6 inch passport photo sheets with zero-gap single-cut borders. Print 8+ photos in 300 DPI studio quality for under ₹10.',
            'h1': 'Passport Photo 4×6 Sheet Maker',
            'canonical': 'https://smartpictools.in/passport-photo-4x6-sheet'
        }
    }
    meta = spokes.get(endpoint)
    return render_template('passport-photo-maker.html', meta=meta)

@app.route('/photo-signature-joiner')
def photo_signature_joiner_page():
    return render_template('photo-signature-joiner.html')

# ⚡ DEDICATED HIGH-INTENT PHOTO & SIGNATURE JOINER SPOKES
@app.route('/ssc-photo-signature-joiner')
@app.route('/up-police-photo-signature-joiner')
def photo_sig_spokes_route():
    endpoint = request.path.strip('/')
    spokes = {
        'ssc-photo-signature-joiner': {
            'preset': 'ssc',
            'title': 'SSC Photo and Signature Joiner Online Free - 350x450 px Under 50KB | SmartPicTools',
            'desc': 'Combine photo and signature for SSC CGL, CHSL, MTS, and GD forms. Official 350x450 px with 80/20 ratio and auto 50KB compression.',
            'h1': 'SSC Photo & Signature Joiner (350 × 450 px)',
            'canonical': 'https://smartpictools.in/ssc-photo-signature-joiner'
        },
        'up-police-photo-signature-joiner': {
            'preset': 'police',
            'title': 'UP Police Photo and Signature Joiner Online Free - 350x500 px Under 50KB | SmartPicTools',
            'desc': 'Join passport photo and signature for UP Police Constable and SI recruitment. Official 350x500 px under 50KB in 300 DPI clarity.',
            'h1': 'UP Police Photo & Signature Joiner (350 × 500 px)',
            'canonical': 'https://smartpictools.in/up-police-photo-signature-joiner'
        }
    }
    meta = spokes.get(endpoint)
    return render_template('photo-signature-joiner.html', meta=meta)

@app.route('/add-name-date-on-photo')
def add_name_date_route():
    return render_template('add-name-date-on-photo.html')
    # ⚡ DEDICATED HIGH-INTENT NAME & DATE ON PHOTO SPOKES
@app.route('/ssc-photo-name-and-date-maker')
@app.route('/up-police-photo-name-date-maker')
def name_date_spokes_route():
    endpoint = request.path.strip('/')
    spokes = {
        'ssc-photo-name-and-date-maker': {
            'title': 'SSC Photo Name and Date Maker Online Free - CGL, CHSL, GD DOP | SmartPicTools',
            'desc': 'Free online tool to add candidate name and Date of Photo (DOP) on passport photo for SSC CGL, CHSL, MTS, and GD in 300 DPI Ultra HD.',
            'h1': 'SSC Photo Name & Date Maker (DOP)',
            'placeholder_date': 'e.g. DOP: 01-11-2026',
            'canonical': 'https://smartpictools.in/ssc-photo-name-and-date-maker'
        },
        'up-police-photo-name-date-maker': {
            'title': 'UP Police Photo Name and Date Maker Online Free - 300 DPI HD | SmartPicTools',
            'desc': 'Generate candidate passport photo with legal name and capture date for UP Police Constable and SI recruitment forms. 100% private in-browser.',
            'h1': 'UP Police Photo Name & Date Maker',
            'placeholder_date': 'e.g. DOP: 01-11-2026',
            'canonical': 'https://smartpictools.in/up-police-photo-name-date-maker'
        }
    }
    meta = spokes.get(endpoint)
    return render_template('add-name-date-on-photo.html', meta=meta)

@app.route('/crop-image')
def crop_route():
    return render_template('crop-image.html')
    # ⚡ DEDICATED HIGH-INTENT CROP IMAGE SPOKES
@app.route('/crop-image-1-1')
@app.route('/crop-image-16-9')
@app.route('/crop-image-9-16')
def crop_spokes_route():
    endpoint = request.path.strip('/')
    spokes = {
        'crop-image-1-1': {
            'ratio': 1.0,
            'preset_key': '1',
            'title': 'Crop Image 1:1 Square Online Free - Professional Aspect Ratio | SmartPicTools',
            'desc': 'Crop photos into perfect 1:1 square aspect ratio online for free. 100% private in-browser tool with zero server uploads.',
            'h1': 'Crop Image 1:1 (Square)',
            'canonical': 'https://smartpictools.in/crop-image-1-1'
        },
        'crop-image-16-9': {
            'ratio': 16 / 9,
            'preset_key': '16/9',
            'title': 'Crop Image 16:9 Horizontal Online Free - Landscape Ratio | SmartPicTools',
            'desc': 'Crop photos into standard 16:9 horizontal landscape aspect ratio online for free. 100% private in-browser tool with zero server uploads.',
            'h1': 'Crop Image 16:9 (Horizontal)',
            'canonical': 'https://smartpictools.in/crop-image-16-9'
        },
        'crop-image-9-16': {
            'ratio': 9 / 16,
            'preset_key': '9/16',
            'title': 'Crop Image 9:16 Vertical Online Free - Fullscreen Aspect Ratio | SmartPicTools',
            'desc': 'Crop photos into 9:16 vertical fullscreen aspect ratio online for free. 100% private in-browser tool with zero server uploads.',
            'h1': 'Crop Image 9:16 (Vertical)',
            'canonical': 'https://smartpictools.in/crop-image-9-16'
        },
        'crop-image-9-16': {
            'ratio': 9 / 16,
            'preset_key': '9/16',
            'title': 'Crop Image 9:16 Online Free - Shorts Cropper | SmartPicTools',
            'desc': 'Crop photos into 9:16 vertical fullscreen format online for free. YouTube Shorts, and TikTok stories without black borders.',
            'h1': 'Crop Image 9:16 (Vertical)',
            'canonical': 'https://smartpictools.in/crop-image-9-16'
        }
    }
    meta = spokes.get(endpoint)
    return render_template('crop-image.html', meta=meta)

@app.route('/resize-image')
def resize_route():
    return render_template('resize-image.html')

# ⚡ DEDICATED HIGH-INTENT RESIZE IMAGE SPOKES
@app.route('/resize-image-200x230')
@app.route('/resize-image-140x60')
@app.route('/resize-image-1000x1000')
def resize_spokes_route():
    endpoint = request.path.strip('/')
    spokes = {
        'resize-image-200x230': {
            'w': 200,
            'h': 230,
            'title': 'Resize Image to 200x230 Pixels Online Free - IBPS & Banking | SmartPicTools',
            'desc': 'Resize photo to exact 200 x 230 pixels online for free. Official dimensions for IBPS, SBI PO, and Clerk application forms. 100% private in-browser.',
            'h1': 'Resize Image to 200 × 230 Pixels',
            'canonical': 'https://smartpictools.in/resize-image-200x230'
        },
        'resize-image-140x60': {
            'w': 140,
            'h': 60,
            'title': 'Resize Signature to 140x60 Pixels Online Free - Banking Form | SmartPicTools',
            'desc': 'Resize signature image to exact 140 x 60 pixels online for free. Official specification for IBPS, Banking, and SSC exam forms without blur.',
            'h1': 'Resize Signature to 140 × 60 Pixels',
            'canonical': 'https://smartpictools.in/resize-image-140x60'
        },
        'resize-image-1000x1000': {
            'w': 1000,
            'h': 1000,
            'title': 'Resize Image to 1000x1000 Pixels Online Free - Square Catalog | SmartPicTools',
            'desc': 'Resize product images to exact 1000 x 1000 pixels square format online for free. Perfect for Meesho, Amazon, Flipkart, and Shopify stores.',
            'h1': 'Resize Image to 1000 × 1000 Pixels',
            'canonical': 'https://smartpictools.in/resize-image-1000x1000'
        }
    }
    meta = spokes.get(endpoint)
    return render_template('resize-image.html', meta=meta)

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
# ⚡ DEDICATED HIGH-INTENT IMAGE TO PDF SPOKES
@app.route('/photo-to-pdf-maker')
@app.route('/jpg-to-pdf-a4')
def image_to_pdf_spokes_route():
    endpoint = request.path.strip('/')
    spokes = {
        'photo-to-pdf-maker': {
            'fit_mode': 'fit',
            'title': 'Photo to PDF Maker Online Free - 0% White Borders | SmartPicTools',
            'desc': 'Convert and merge multiple photos into single PDF online for free with edge-to-edge full fit and zero white margins. 100% private in-browser.',
            'h1': 'Photo to PDF Maker (Edge-to-Edge)',
            'canonical': 'https://smartpictools.in/photo-to-pdf-maker'
        },
        'jpg-to-pdf-a4': {
            'fit_mode': 'a4',
            'title': 'Convert JPG to PDF A4 Online Free - Standard Document Size | SmartPicTools',
            'desc': 'Convert JPG, PNG, and images to standard A4 PDF document online for free. Official size for college assignments, office, and official submissions.',
            'h1': 'Convert JPG to PDF (A4 Document Size)',
            'canonical': 'https://smartpictools.in/jpg-to-pdf-a4'
        }
    }
    meta = spokes.get(endpoint)
    return render_template('image-to-pdf.html', meta=meta)

@app.route('/crop-pdf')
def crop_pdf_page():
    return render_template('crop-pdf.html')

@app.route('/split-pdf')
def split_pdf_page():
    return render_template('split-pdf.html')

# ⚡ YOUTUBE THUMBNAIL DOWNLOADER ROUTES
@app.route('/youtube-thumbnail-downloader')
@app.route('/yt-thumbnail-downloader')
def yt_thumbnail_page():
    return render_template('youtube-thumbnail-downloader.html')

# ⚡ DIRECT ATTACHMENT STREAM (PREVENTS OPENING IN NEW TAB ON MOBILE)
# ⚡ YOUTUBE THUMBNAIL ENGINE (4K, 1080P, 720P & 9:16 SHORTS CROPPER)
@app.route('/get-yt-thumb')
def get_yt_thumb():
    import urllib.request
    vid = request.args.get('id', '')
    res = request.args.get('res', '1080p').lower()
    is_shorts = request.args.get('shorts', 'false').lower() == 'true'

    if not vid or len(vid) != 11:
        return jsonify({'error': 'Invalid video ID'}), 400

    raw_data = None
    for q_name in ['maxresdefault', 'hqdefault']:
        try:
            url = f"https://img.youtube.com/vi/{vid}/{q_name}.jpg"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            resp = urllib.request.urlopen(req)
            data = resp.read()
            if len(data) > 2500:
                raw_data = data
                break
        except Exception:
            continue

    if not raw_data:
        return redirect(f"https://img.youtube.com/vi/{vid}/hqdefault.jpg")

    try:
        img = Image.open(io.BytesIO(raw_data)).convert('RGB')

        # ⚡ 9:16 Shorts Crop (Cuts off blurred sidebars)
        if is_shorts:
            target_aspect = 9.0 / 16.0
            crop_w = int(img.height * target_aspect)
            crop_x = (img.width - crop_w) // 2
            img = img.crop((crop_x, 0, crop_x + crop_w, img.height))
            sizes = {'4k': (2160, 3840), '1080p': (1080, 1920), '720p': (720, 1280), '480p': (480, 854)}
        else:
            sizes = {'4k': (3840, 2160), '1080p': (1920, 1080), '720p': (1280, 720), '480p': (854, 480)}

        target_size = sizes.get(res, sizes['1080p'])
        img = img.resize(target_size, Image.Resampling.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=95)
        buf.seek(0)

        out_label = f"shorts_{res}" if is_shorts else f"video_{res}"
        return send_file(buf, mimetype='image/jpeg', as_attachment=True, download_name=f"yt_thumb_{vid}_{out_label}.jpg")
    except Exception:
        return send_file(io.BytesIO(raw_data), mimetype='image/jpeg', as_attachment=True, download_name=f"yt_thumb_{vid}.jpg")


# ⚡ PDF PASSWORD PROTECT & UNLOCK ROUTES
@app.route('/pdf-password')
@app.route('/protect-pdf')
@app.route('/unlock-pdf')
def pdf_password_page():
    return render_template('pdf-password.html')

# 301 Permanent Redirects to Preserve Google SEO Juice (Zero 404 Errors)
@app.route('/pdf-converter')
def pdf_converter_alias():
    return redirect('/convert-from-pdf', code=301)

@app.route('/meesho-image-generator')
@app.route('/meesho-low-shipping')
@app.route('/download-meesho-extension')
def meesho_clean_redirect():
    return redirect('/', code=301)

# ==========================================
# ⚡ SUGGESTION BOX (FORMSUBMIT & API BACKUP)
# ==========================================
@app.route('/api/submit-suggestion', methods=['POST'])
def submit_suggestion():
    try:
        data = request.get_json(silent=True) or request.form
        name = data.get('name', 'Anonymous')
        email = data.get('email', 'Not provided')
        msg = data.get('message', '')
        print(f"⚡ [SUGGESTION] From: {name} ({email}) | Message: {msg}")
        return jsonify({'status': 'success', 'message': 'Thank you! Your feedback has been received.'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ==========================================
# ⚡ MILITARY-GRADE AES-256 PDF ENCRYPTION & UNLOCK ENGINE
# ==========================================
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
            doc.save(buf, encryption=fitz.PDF_ENCRYPT_AES_256, user_pw=password, owner_pw=password)
            doc.close()
            buf.seek(0)
            return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name=f"{raw_name}_protected.pdf")
        else:
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
            
            doc.save(buf, encryption=fitz.PDF_ENCRYPT_NONE)
            doc.close()
            buf.seek(0)
            return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name=f"{raw_name}_unlocked.pdf")

    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
    
    for y in range(size):
        ratio = y / float(size)
        r = int(99 + (236 - 99) * ratio)
        g = int(102 + (72 - 102) * ratio)
        b = int(241 + (153 - 241) * ratio)
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))
        
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    corner_radius = int(size * 0.28)
    mask_draw.rounded_rectangle([0, 0, size, size], radius=corner_radius, fill=255)
    img.putalpha(mask)
    
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
    today = datetime.date.today().isoformat()
    urls = [
        ('https://smartpictools.in/', '1.0'),
        ('https://smartpictools.in/compress-image', '0.9'),
        ('https://smartpictools.in/compress-image-to-20kb', '0.9'),
        ('https://smartpictools.in/compress-image-to-50kb', '0.9'),
        ('https://smartpictools.in/compress-image-to-100kb', '0.9'),
        ('https://smartpictools.in/passport-photo-maker', '0.9'),
        ('https://smartpictools.in/passport-photo-3.5x4.5-cm', '0.9'),
        ('https://smartpictools.in/2x2-inch-visa-photo-maker', '0.9'),
        ('https://smartpictools.in/passport-photo-4x6-sheet', '0.9'),
        ('https://smartpictools.in/photo-signature-joiner', '0.9'),
        ('https://smartpictools.in/ssc-photo-signature-joiner', '0.9'),
        ('https://smartpictools.in/up-police-photo-signature-joiner', '0.9'),
        ('https://smartpictools.in/add-name-date-on-photo', '0.9'),
        ('https://smartpictools.in/ssc-photo-name-and-date-maker', '0.9'),
        ('https://smartpictools.in/up-police-photo-name-date-maker', '0.9'),
        ('https://smartpictools.in/crop-image', '0.9'),
        ('https://smartpictools.in/crop-image-1-1', '0.9'),
        ('https://smartpictools.in/crop-image-16-9', '0.9'),
        ('https://smartpictools.in/crop-image-9-16', '0.9'),
        ('https://smartpictools.in/resize-image', '0.9'),
        ('https://smartpictools.in/resize-image-200x230', '0.9'),
        ('https://smartpictools.in/resize-image-140x60', '0.9'),
        ('https://smartpictools.in/resize-image-1000x1000', '0.9'),
        ('https://smartpictools.in/convert-image', '0.9'),
        ('https://smartpictools.in/crop-pdf', '0.9'),
        ('https://smartpictools.in/image-to-pdf', '0.9'),
        ('https://smartpictools.in/photo-to-pdf-maker', '0.9'),
        ('https://smartpictools.in/jpg-to-pdf-a4', '0.9'),
        ('https://smartpictools.in/split-pdf', '0.9'),
        ('https://smartpictools.in/youtube-thumbnail-downloader', '0.9'),
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
        xml.append(f'  <url><loc>{u}</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>{p}</priority></url>')
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
    ads_content = "google.com, pub-6941008868816067, DIRECT, f08c47fec0942fa0\n"
    return Response(ads_content, mimetype='text/plain')

@app.route('/google1c187c8e8addbbb4.html')
def google_verify():
    return 'google-site-verification: google1c187c8e8addbbb4.html'

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
# ⚡ TURBO 1-SECOND AVIF & FALLBACK ENGINE
# ==========================================
@app.route('/process', methods=['POST'])
def process_fallback():
    try:
        file = request.files.get('image')
        target_fmt = request.form.get('format', 'AVIF').upper()
        if not file:
            return jsonify({'error': 'No file provided'}), 400

        img = Image.open(io.BytesIO(file.read()))
        
        # Fast RGB convert
        if img.mode != 'RGB':
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                bg = Image.new('RGB', img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[3] if len(img.split()) > 3 else None)
                img = bg
            else:
                img = img.convert('RGB')

        # Fast Bilinear downscale for sub-second web speed
        if img.width > 1280 or img.height > 1280:
            img.thumbnail((1280, 1280), Image.Resampling.BILINEAR)

        buf = io.BytesIO()
        out_name = f"smartpic_converted.{target_fmt.lower()}"
        mimetype = f"image/{target_fmt.lower()}"

        if target_fmt == 'AVIF':
            saved = False
            try:
                img.save(buf, format='AVIF', quality=55, speed=10)
                saved = True
            except Exception:
                try:
                    img.save(buf, format='AVIF', quality=55)
                    saved = True
                except Exception:
                    pass
            
            if not saved:
                import pillow_heif
                heif_file = pillow_heif.from_pillow(img)
                heif_file.save(buf, format="AVIF", quality=55)

        elif target_fmt in ['JPG', 'JPEG']:
            img.save(buf, format='JPEG', quality=85)
            mimetype = 'image/jpeg'
        elif target_fmt == 'PNG':
            img.save(buf, format='PNG')
        elif target_fmt == 'WEBP':
            img.save(buf, format='WEBP', quality=80)
        elif target_fmt in ['TIFF', 'TIF']:
            img.save(buf, format='TIFF')
            mimetype = 'image/tiff'

        buf.seek(0)
        return send_file(buf, mimetype=mimetype, as_attachment=True, download_name=out_name)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
