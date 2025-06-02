import os
import tempfile
import uuid
from flask import Flask, render_template, request, jsonify, send_file, Response
from werkzeug.utils import secure_filename
import cv2
import io
import numpy as np
from crypto_utils import encrypt_message, decrypt_message
from stego_utils import embed_message, extract_message

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Use a temporary directory for file operations
TEMP_DIR = tempfile.gettempdir()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tiff'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def text_to_binary(text):
    return ''.join(format(byte, '08b') for byte in text.encode())

def binary_to_text(binary_data):
    byte_list = [binary_data[i:i+8] for i in range(0, len(binary_data), 8)]
    return bytes([int(b, 2) for b in byte_list])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encode', methods=['POST'])
def encode():
    if 'image' not in request.files or 'message' not in request.files:
        return jsonify({'error': 'Missing required files'}), 400
    
    image_file = request.files['image']
    text_file = request.files['message']
    private_key = request.form.get('private_key', '')
    public_key = request.form.get('public_key', '')
    
    if not (private_key and public_key):
        return jsonify({'error': 'Both private and public keys are required'}), 400
    
    if image_file.filename == '' or text_file.filename == '':
        return jsonify({'error': 'No selected files'}), 400
    
    if not (image_file and allowed_file(image_file.filename)):
        return jsonify({'error': 'Invalid image file. Only PNG, JPG, JPEG, BMP, and TIFF files are allowed.'}), 400
    
    try:
        # Read image file into memory
        image_data = image_file.read()
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({'error': 'Could not process the image. Please try a different image file.'}), 400
            
        # Read message from text file
        message = text_file.read().decode('utf-8')
        
        # Generate shared key
        try:
            private_key_int = int(private_key)
            public_key_int = int(public_key)
            shared_key = str(pow(public_key_int, private_key_int, 23)).encode()
            shared_key = shared_key.ljust(32, b'\0')[:32]  # Ensure 32-byte key
        except ValueError:
            return jsonify({'error': 'Invalid key format. Please use numeric keys.'}), 400
        
        # Create a temporary file for the output
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            output_path = temp_file.name
        
        try:
            # Encode message in image
            embed_message(img, message, shared_key, output_path)
            
            # Read the encoded image back into memory
            with open(output_path, 'rb') as f:
                encoded_image = io.BytesIO(f.read())
            
            # Return the encoded image for download
            return send_file(
                encoded_image,
                mimetype='image/png',
                as_attachment=True,
                download_name='encoded_image.png'
            )
        finally:
            # Clean up the temporary file
            try:
                os.unlink(output_path)
            except:
                pass
        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/decode', methods=['POST'])
def decode():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    image_file = request.files['image']
    private_key = request.form.get('private_key', '')
    public_key = request.form.get('public_key', '')
    
    if not (private_key and public_key):
        return jsonify({'error': 'Both private and public keys are required'}), 400
    
    if image_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    try:
        # Read image file into memory
        image_data = image_file.read()
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({'error': 'Could not process the image. Please try a different image file.'}), 400
        
        # Generate shared key
        try:
            private_key_int = int(private_key)
            public_key_int = int(public_key)
            shared_key = str(pow(public_key_int, private_key_int, 23)).encode()
            shared_key = shared_key.ljust(32, b'\0')[:32]  # Ensure 32-byte key
        except ValueError:
            return jsonify({'error': 'Invalid key format. Please use numeric keys.'}), 400
        
        # Extract message from the image
        try:
            decrypted_message = extract_message(img, shared_key)
            
            # Ensure the message is a string
            if isinstance(decrypted_message, bytes):
                try:
                    decrypted_message = decrypted_message.decode('utf-8', errors='replace')
                except UnicodeDecodeError:
                    # If UTF-8 decoding fails, return as base64
                    import base64
                    decrypted_message = base64.b64encode(decrypted_message).decode('ascii')
            
            return jsonify({
                'message': decrypted_message,
                'is_base64': not isinstance(decrypted_message, str) or not decrypted_message.isprintable()
            })
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
