from flask import Flask, request, jsonify, send_from_directory, render_template_string
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Folder for uploaded files
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = set()  # Empty = allow all extensions

def allowed_file(filename):
    """Optionally restrict file extensions."""
    return '.' in filename and (not ALLOWED_EXTENSIONS or filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS)

@app.route('/')
def index():
    """Serve your HTML interface."""
    with open("index.html", "r", encoding="utf-8") as f:
        return render_template_string(f.read())

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle multiple file uploads of any type."""
    if 'files' not in request.files:
        return jsonify({'error': 'No files part in request'}), 400

    files = request.files.getlist('files')
    uploaded_files = []

    for file in files:
        if file.filename == '':
            continue
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            uploaded_files.append({
                'name': filename,
                'url': f'/uploads/{filename}'
            })

    return jsonify({'files': uploaded_files})

@app.route('/uploads/<path:filename>')
def serve_file(filename):
    """Serve uploaded files."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
