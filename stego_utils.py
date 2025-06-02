import cv2
import zlib
import numpy as np
from crypto_utils import encrypt_message, decrypt_message

def text_to_binary(text):
    if isinstance(text, str):
        text = text.encode('utf-8')
    return ''.join(format(byte, '08b') for byte in text)

def binary_to_text(binary_data):
    byte_list = [binary_data[i:i+8] for i in range(0, len(binary_data), 8)]
    try:
        return bytes([int(b, 2) for b in byte_list if b])
    except (ValueError, IndexError):
        return b''

def embed_message(img, message, key, output_path):
    try:
        # Ensure message is bytes
        if isinstance(message, str):
            message = message.encode('utf-8')
            
        # Encrypt the message
        encrypted_message = encrypt_message(message, key)
        
        # Compress the encrypted message
        compressed_message = zlib.compress(encrypted_message)
        
        # Convert to binary and add end marker
        binary_message = text_to_binary(compressed_message) + '1111111111111110'

        h, w, _ = img.shape
        total_pixels = h * w * 3 * 2  # 2 bits per color channel per pixel

        if len(binary_message) > total_pixels:
            raise ValueError(f"Message too long to fit in the image. Max: {total_pixels // 8} bytes")

        binary_index = 0
        message_length = len(binary_message)
        
        # Create a copy of the image to avoid modifying the original
        img_copy = img.copy()
        
        for i in range(h):
            for j in range(w):
                for k in range(3):  # Iterate over BGR channels
                    if binary_index < message_length - 1:
                        # Get next 2 bits
                        two_bits = binary_message[binary_index:binary_index+2].ljust(2, '0')
                        # Clear the last 2 bits and set the new ones
                        img_copy[i, j, k] = (img_copy[i, j, k] & 0xFC) | int(two_bits, 2)
                        binary_index += 2
                    else:
                        # If we've encoded all bits, save and return
                        success = cv2.imwrite(output_path, img_copy)
                        if not success:
                            raise ValueError("Failed to save the encoded image")
                        return
                        
        # If we've processed all pixels but still have bits left (shouldn't happen due to size check)
        success = cv2.imwrite(output_path, img_copy)
        if not success:
            raise ValueError("Failed to save the encoded image")
            
    except Exception as e:
        raise ValueError(f"Error in embed_message: {str(e)}")

def extract_message(img, key):
    try:
        h, w, _ = img.shape
        binary_message = ""
        
        # Limit processing for performance
        max_pixels = 1000 * 1000  # 1MP max for processing
        if h * w > max_pixels:
            # Resize the image if it's too large
            ratio = (max_pixels / (h * w)) ** 0.5
            new_h, new_w = int(h * ratio), int(w * ratio)
            img = cv2.resize(img, (new_w, new_h))
            h, w = new_h, new_w
        
        # Extract LSBs from the image
        for i in range(h):
            for j in range(w):
                for k in range(3):  # BGR channels
                    binary_message += format(img[i, j, k], '08b')[-2:]
        
        end_marker = '1111111111111110'
        end_index = binary_message.find(end_marker)
        
        if end_index == -1:
            raise ValueError("No hidden message found in the image")
        
        binary_message = binary_message[:end_index]
        extracted_data = binary_to_text(binary_message)
        
        if not extracted_data:
            raise ValueError("Failed to extract binary data from image")
        
        # Try to decompress and decrypt
        try:
            decompressed_message = zlib.decompress(extracted_data)
            decrypted_message = decrypt_message(decompressed_message, key)
            return decrypted_message
        except zlib.error as e:
            # If decompression fails, try to decrypt directly
            try:
                return decrypt_message(extracted_data, key)
            except Exception as e2:
                raise ValueError(f"Failed to process message: {str(e2)}")
        except Exception as e:
            raise ValueError(f"Failed to decrypt message: {str(e)}")
            
    except Exception as e:
        raise ValueError(f"Error extracting message: {str(e)}")
