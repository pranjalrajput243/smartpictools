import io
import os
import json
import datetime
from flask import Flask, render_template, request, send_file, jsonify
from PIL import Image

# Import Modular Tools (Plugins)
from tools import compress, resize, crop, watermark, convert, rotate

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

@app.route('/process', methods=['POST'])
def process_image():
    try:
        files = request.files.getlist('image')
        tool = request.form.get('tool', 'compress')
        
        if not files or files[0].filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Routing requests to respective plugin
        if tool == 'compress':
            file = files[0]
            filename, orig_ext = os.path.splitext(file.filename)
            img = Image.open(io.BytesIO(file.read()))
            data, mime, name = compress.process(request, img, filename, orig_ext)
            
        elif tool == 'resize':
            file = files[0]
            filename, orig_ext = os.path.splitext(file.filename)
            img = Image.open(io.BytesIO(file.read()))
            data, mime, name = resize.process(request, img, filename, orig_ext)
            
        elif tool == 'crop':
            file = files[0]
            filename, orig_ext = os.path.splitext(file.filename)
            img = Image.open(io.BytesIO(file.read()))
            data, mime, name = crop.process(request, img, filename, orig_ext)
            
        elif tool == 'watermark':
            file = files[0]
            filename, orig_ext = os.path.splitext(file.filename)
            img = Image.open(io.BytesIO(file.read()))
            data, mime, name = watermark.process(request, img, filename, orig_ext)
            
        elif tool == 'rotate':
            file = files[0]
            filename, orig_ext = os.path.splitext(file.filename)
            img = Image.open(io.BytesIO(file.read()))
            data, mime, name = rotate.process(request, img, filename, orig_ext)
            
        elif tool == 'convert':
            file = files[0]
            filename, orig_ext = os.path.splitext(file.filename)
            img = Image.open(io.BytesIO(file.read()))
            data, mime, name = convert.process(request, img, filename, orig_ext, files=files)
            
        else:
            return jsonify({'error': 'Invalid tool selected'}), 400

        return send_file(
            io.BytesIO(data),
            mimetype=mime,
            as_attachment=True,
            download_name=name
        )

    except Exception as e:
        print("Backend Error:", str(e))
        return jsonify({'error': f"Processing failed: {str(e)}"}), 500

if __name__ == '__main__':
    print("\n---------------------------------------------------------")
    print(" 🚀 SmartPicTools Modular Server Live (PC & Mobile Ready) ")
    print(" Local PC:  http://127.0.0.1:5000 ")
    print("---------------------------------------------------------\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
