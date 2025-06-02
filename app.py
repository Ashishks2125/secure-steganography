import os
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import cv2
import io
from crypto_utils import encrypt_message, decrypt_message
from stego_utils import embed_message, extract_message

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
        return jsonify({'error': 'Invalid image file'}), 400
    
    try:
        # Save uploaded files
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(image_file.filename))
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'encoded_' + secure_filename(image_file.filename))
        
        image_file.save(image_path)
        
        # Read message from text file
        message = text_file.read().decode('utf-8')
        
        # Generate shared key (simplified for web)
        try:
            private_key_int = int(private_key)
            public_key_int = int(public_key)
            shared_key = str(pow(public_key_int, private_key_int, 23)).encode()
            shared_key = shared_key.ljust(32, b'\0')[:32]  # Ensure 32-byte key
        except ValueError:
            return jsonify({'error': 'Invalid key format'}), 400
        
        # Read and process image
        img = cv2.imread(image_path)
        if img is None:
            return jsonify({'error': 'Could not process the image'}), 400
        
        # Encode message in image
        embed_message(img, message, shared_key, output_path)
        
        # Return the encoded image for download
        return send_file(
            output_path,
            mimetype='image/png',
            as_attachment=True,
            download_name='encoded_image.png'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        # Save uploaded file
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(image_file.filename))
        image_file.save(image_path)
        
        # Generate shared key (simplified for web)
        try:
            private_key_int = int(private_key)
            public_key_int = int(public_key)
            shared_key = str(pow(public_key_int, private_key_int, 23)).encode()
            shared_key = shared_key.ljust(32, b'\0')[:32]  # Ensure 32-byte key
        except ValueError:
            return jsonify({'error': 'Invalid key format'}), 400
        
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            return jsonify({'error': 'Could not process the image'}), 400
        
        # Extract message from image
        binary_message = ""
        h, w, _ = img.shape
        
        for i in range(h):
            for j in range(w):
                for k in range(3):
                    binary_message += format(img[i, j, k], '08b')[-2:]
        
        end_marker = '1111111111111110'
        end_index = binary_message.find(end_marker)
        if end_index == -1:
            return jsonify({'error': 'No hidden message found'}), 400
        
        binary_message = binary_message[:end_index]
        extracted_data = binary_to_text(binary_message)
        
        try:
            import zlib
            decompressed_message = zlib.decompress(extracted_data)
            decrypted_message = decrypt_message(decompressed_message, shared_key)
            return jsonify({'message': decrypted_message})
        except Exception as e:
            return jsonify({'error': 'Failed to decrypt message. Incorrect key?'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
