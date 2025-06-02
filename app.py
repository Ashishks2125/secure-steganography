import os
import tempfile
import io
import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify, send_file, Response
from werkzeug.utils import secure_filename
from crypto_utils import encrypt_message, decrypt_message
from stego_utils import embed_message, extract_message

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Use system's temp directory
TEMP_DIR = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tiff'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def text_to_binary(text):
    if isinstance(text, str):
        text = text.encode('utf-8')
    return ''.join(format(byte, '08b') for byte in text)

def binary_to_text(binary_data):
    byte_list = [binary_data[i:i+8] for i in range(0, len(binary_data), 8)]
    try:
        return bytes([int(b, 2) for b in byte_list])
    except ValueError:
        return b''

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encode', methods=['POST'])
def encode():
    try:
        # Check if the request contains the required fields
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
            
        file = request.files['image']
        
        # Get message and key from form data
        message = request.form.get('message', '')
        key = request.form.get('key', '')
        
        # Validate required fields
        if not message:
            return jsonify({'error': 'Message is required'}), 400
            
        if not key:
            return jsonify({'error': 'Encryption key is required'}), 400
            
        if not key.isdigit():
            return jsonify({'error': 'Key must be a numeric value'}), 400
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if not allowed_file(file.filename):
            return jsonify({
                'error': 'Invalid file type. Allowed types are: ' + ', '.join(ALLOWED_EXTENSIONS)
            }), 400
        
        # Read and validate image
        try:
            file_content = file.read()
            nparr = np.frombuffer(file_content, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None or img.size == 0:
                return jsonify({'error': 'Invalid or corrupted image file'}), 400
                
            # Limit image size for performance
            max_dimension = 5000
            if img.shape[0] > max_dimension or img.shape[1] > max_dimension:
                return jsonify({
                    'error': f'Image dimensions are too large. Maximum allowed dimension is {max_dimension}x{max_dimension} pixels.'
                }), 400
            
            # Create a temporary file for the output
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                output_path = temp_file.name
            
            try:
                # Process the image
                embed_message(img, message, key, output_path)
                
                # Read the processed image back into memory
                with open(output_path, 'rb') as f:
                    encoded_image = f.read()
                
                # Clean up the temporary file
                try:
                    os.unlink(output_path)
                except OSError:
                    pass
                
                # Return the image as a response
                return send_file(
                    io.BytesIO(encoded_image),
                    mimetype='image/png',
                    as_attachment=True,
                    download_name='encoded_image.png',
                    max_age=0  # Prevent caching
                )
                
            except ValueError as ve:
                return jsonify({'error': str(ve)}), 400
            except Exception as e:
                app.logger.error(f"Error during encoding: {str(e)}", exc_info=True)
                return jsonify({'error': 'An error occurred during image encoding'}), 500
            finally:
                # Ensure temp file is cleaned up
                if os.path.exists(output_path):
                    try:
                        os.unlink(output_path)
                    except OSError:
                        pass
                    
        except Exception as e:
            app.logger.error(f"Error processing image: {str(e)}", exc_info=True)
            return jsonify({'error': 'Failed to process the uploaded image'}), 400
            
    except Exception as e:
        app.logger.error(f"Unexpected error in /encode: {str(e)}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/decode', methods=['POST'])
def decode():
    """Handle message extraction from an image."""
    try:
        # Check if the request contains the required fields
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
            
        file = request.files['image']
        key = request.form.get('key', '')
        
        # Validate required fields
        if not key:
            return jsonify({'error': 'Decryption key is required'}), 400
            
        if not key.isdigit():
            return jsonify({'error': 'Key must be a numeric value'}), 400
            
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if not allowed_file(file.filename):
            return jsonify({
                'error': 'Invalid file type. Allowed types are: ' + ', '.join(ALLOWED_EXTENSIONS)
            }), 400
        
        # Read and validate image
        try:
            file_content = file.read()
            nparr = np.frombuffer(file_content, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None or img.size == 0:
                return jsonify({'error': 'Invalid or corrupted image file'}), 400
                
            # Limit image size for performance
            max_dimension = 5000
            if img.shape[0] > max_dimension or img.shape[1] > max_dimension:
                return jsonify({
                    'error': f'Image dimensions are too large. Maximum allowed dimension is {max_dimension}x{max_dimension} pixels.'
                }), 400
            
            # Extract the message
            try:
                result = extract_message(img, key)
                
                if result is None:
                    return jsonify({'error': 'No message found in the image or incorrect key'}), 400
                    
                if isinstance(result, bytes):
                    # If the result is binary, return it as a file
                    return send_file(
                        io.BytesIO(result),
                        mimetype='application/octet-stream',
                        as_attachment=True,
                        download_name='extracted_message.bin',
                        max_age=0  # Prevent caching
                    )
                else:
                    # If the result is text, return it as JSON
                    return jsonify({
                        'message': result,
                        'is_text': True
                    })
                    
            except ValueError as ve:
                return jsonify({'error': str(ve)}), 400
            except Exception as e:
                app.logger.error(f"Error during decoding: {str(e)}", exc_info=True)
                return jsonify({'error': 'An error occurred while extracting the message'}), 400
                
        except Exception as e:
            app.logger.error(f"Error processing image: {str(e)}", exc_info=True)
            return jsonify({'error': 'Failed to process the uploaded image'}), 400
            
    except Exception as e:
        app.logger.error(f"Unexpected error in /decode: {str(e)}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500

if __name__ == '__main__':
    app.run(debug=True)
