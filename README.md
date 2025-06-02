# Secure Image Steganography Web Application

A web-based application that allows users to hide secret messages within images using steganography and encryption.

## Features

- **Encode**: Hide a secret message within an image
- **Decode**: Extract a hidden message from an encoded image
- **Secure**: Uses AES-256 encryption with Diffie-Hellman key exchange
- **User-friendly**: Simple web interface for easy use

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Installation

1. Clone the repository or download the source code
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Running the Application

1. Start the Flask development server:
   ```
   python app.py
   ```
2. Open your web browser and navigate to `http://localhost:5000`

## How to Use

### Encoding a Message

1. Select the "Encode" tab
2. Upload a text file containing your secret message
3. Upload an image to hide the message in
4. Enter your private key (a number between 1-22)
5. Enter the recipient's public key
6. Click "Encode Message"
7. The encoded image will be automatically downloaded

### Decoding a Message

1. Select the "Decode" tab
2. Upload the encoded image
3. Enter your private key
4. Enter the sender's public key
5. Click "Decode Message"
6. The hidden message will be displayed

### Key Generation

1. In the "Key Generation" section, enter a private key (a number between 1-22)
2. Click "Calculate" to generate your public key
3. Share your public key with others
4. Keep your private key secret

## Security Notes

- Always use strong, unique private keys
- Never share your private key
- The application uses AES-256 encryption for message security
- For production use, consider using HTTPS to secure the connection

## License

This project is open source and available under the MIT License.
