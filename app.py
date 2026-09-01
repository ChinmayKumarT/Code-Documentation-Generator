import os
import shutil
import tempfile
import time
import uuid
# Fix protobuf compatibility issue
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
from flask import Flask, request, render_template, jsonify, send_from_directory, send_file
from werkzeug.utils import secure_filename
from analyzer.report_generator import generate_report

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['TEMP_FOLDER'] = 'temp'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload, output, and temp directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

# Allowed file extensions
# Keep in sync with the parsers registered in analyzer.code_parser.get_parser
ALLOWED_EXTENSIONS = {
    'py': 'python',
    'js': 'javascript',
    'ts': 'typescript',
    'java': 'java',
    'c': 'c',
    'h': 'c',
    'cpp': 'cpp',
    'cc': 'cpp',
    'hpp': 'cpp'
}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Generated reports stay on disk so the browser can download them. Nothing
# else removes them, so sweep old sessions before creating a new one.
SESSION_TTL_SECONDS = int(os.environ.get('SESSION_TTL_SECONDS', 3600))

def cleanup_old_sessions():
    """Delete report directories older than SESSION_TTL_SECONDS."""
    root = app.config['TEMP_FOLDER']
    cutoff = time.time() - SESSION_TTL_SECONDS
    try:
        entries = os.listdir(root)
    except OSError:
        return
    for name in entries:
        path = os.path.join(root, name)
        try:
            if os.path.isdir(path) and os.path.getmtime(path) < cutoff:
                shutil.rmtree(path, ignore_errors=True)
        except OSError:
            # A sweep failure must never break the request that triggered it
            pass

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def handle_upload():
    try:
        # Check if the post request has the file part or code
        if 'file' in request.files and request.files['file'].filename != '':
            return handle_file_upload()
        elif 'code' in request.form and request.form['code'].strip() != '':
            return handle_code_paste()
        else:
            return jsonify({'error': 'No file or code provided'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/paste', methods=['POST'])
def handle_paste():
    return handle_code_paste()

def handle_file_upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not supported'}), 400
    
    try:
        cleanup_old_sessions()

        # Create a unique ID for this session
        session_id = str(uuid.uuid4())
        base_filename = os.path.splitext(secure_filename(file.filename))[0]
        
        # Create a unique temp directory for this upload
        temp_dir = os.path.join(app.config['TEMP_FOLDER'], session_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save the uploaded file with a unique name
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{session_id}{file_extension}"
        filepath = os.path.join(temp_dir, unique_filename)
        file.save(filepath)
        
        # Generate reports in the temp directory
        generate_report(filepath, output_dir=temp_dir,
                        display_name=secure_filename(file.filename))

        # Prepare response with download links
        response_files = {}
        for ext in ['json', 'pdf', 'md']:
            source = os.path.join(temp_dir, f'report.{ext}')
            if os.path.exists(source):
                # Create a more descriptive filename
                dest_filename = f"{base_filename}_report.{ext}"
                dest_path = os.path.join(temp_dir, dest_filename)

                # Remove destination if it exists
                if os.path.exists(dest_path):
                    os.unlink(dest_path)

                # Rename the file
                os.rename(source, dest_path)

                # Add to response with session ID in the URL
                response_files[ext] = {
                    'url': f"/download/{session_id}/{dest_filename}",
                    'filename': dest_filename
                }

        return jsonify({
            'message': 'Report generated successfully',
            'files': response_files
        })

    except (ValueError, SyntaxError) as e:
        # Bad input, not a server fault
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def handle_code_paste():
    if 'code' not in request.form or not request.form['code'].strip():
        return jsonify({'error': 'No code provided'}), 400
    
    code = request.form['code'].strip()
    language = request.form.get('language', 'txt')
    
    # Map language to file extension
    ext_map = {
        'python': 'py',
        'javascript': 'js',
        'java': 'java',
        'c': 'c',
        'cpp': 'cpp',
        'txt': 'txt'
    }
    
    file_extension = f".{ext_map.get(language, 'txt')}"
    filename = f"code{file_extension}"
    
    try:
        cleanup_old_sessions()

        # Create a unique ID for this session
        session_id = str(uuid.uuid4())
        base_filename = f"code_{language}"  # More descriptive base name
        
        # Create a unique temp directory for this paste
        temp_dir = os.path.join(app.config['TEMP_FOLDER'], session_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save the pasted code to a file with proper extension
        unique_filename = f"{session_id}{file_extension}"
        filepath = os.path.join(temp_dir, unique_filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # Generate reports in the temp directory
        generate_report(filepath, output_dir=temp_dir, display_name=filename)

        # Prepare response with download links
        response_files = {}
        for ext in ['json', 'pdf', 'md']:
            source = os.path.join(temp_dir, f'report.{ext}')
            if os.path.exists(source):
                # Create a more descriptive filename
                dest_filename = f"{base_filename}_report.{ext}"
                dest_path = os.path.join(temp_dir, dest_filename)
                
                # Remove destination if it exists
                if os.path.exists(dest_path):
                    os.unlink(dest_path)
                
                # Rename the file
                os.rename(source, dest_path)
                
                # Add to response with session ID in the URL
                response_files[ext] = {
                    'url': f"/download/{session_id}/{dest_filename}",
                    'filename': dest_filename
                }
        
        return jsonify({
            'message': 'Report generated successfully',
            'files': response_files
        })
        
    except (ValueError, SyntaxError) as e:
        # Bad input, not a server fault
        return jsonify({'error': f'Error processing code: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Error processing code: {str(e)}'}), 500

@app.route('/download/<session_id>/<path:filename>')
def download_file(session_id, filename):
    temp_dir = os.path.join(app.config['TEMP_FOLDER'], session_id)
    if not os.path.exists(temp_dir):
        return "File not found", 404
    return send_from_directory(temp_dir, filename, as_attachment=True, download_name=filename)

if __name__ == '__main__':
    # Local development only. In production the app is served by gunicorn
    # (see Dockerfile / Procfile) and this block never runs.
    # FLASK_DEBUG=1 enables the Werkzeug debugger, which grants a remote
    # Python console — never set it on a public host.
    debug = os.environ.get('FLASK_DEBUG') == '1'
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)
