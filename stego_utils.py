import cv2
import zlib
from crypto_utils import encrypt_message, decrypt_message

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

def embed_message(img, message, key, output_path):
    try:
        if isinstance(message, str):
            message = message.encode('utf-8')
            
        encrypted_message = encrypt_message(message, key)
        compressed_message = zlib.compress(encrypted_message)
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

def extract_message(img, key, max_pixels=1000000):
    """
    Extract a hidden message from an image.
    
    Args:
        img: The image containing the hidden message
        key: The encryption key
        max_pixels: Maximum number of pixels to process (for performance)
        
    Returns:
        str: The extracted message, or None if no message found
    """
    try:
        h, w, _ = img.shape
        total_pixels = h * w
        
        # If image is too large, process only a portion of it
        if total_pixels > max_pixels:
            # Calculate dimensions to maintain aspect ratio
            ratio = (max_pixels / total_pixels) ** 0.5
            new_h = int(h * ratio)
            new_w = int(w * ratio)
            img = cv2.resize(img, (new_w, new_h))
            h, w = new_h, new_w
        
        binary_message = []
        end_marker = '1111111111111110'
        marker_length = len(end_marker)
        
        # Process the image in chunks for better performance
        for i in range(h):
            row_bits = []
            for j in range(w):
                # Get the last 2 bits of each color channel (BGR)
                for k in range(3):
                    row_bits.append(format(img[i, j, k], '08b')[-2:])
            
            # Join the bits for this row and add to our message
            row_bits = ''.join(row_bits)
            binary_message.append(row_bits)
            
            # Check if we've found the end marker in the current binary message
            current_message = ''.join(binary_message)
            end_index = current_message.find(end_marker)
            
            if end_index != -1:
                # Found the end marker, extract the message
                binary_data = current_message[:end_index]
                extracted_data = binary_to_text(binary_data)
                
                if not extracted_data:
                    raise ValueError("Failed to convert binary data to bytes")
                
                try:
                    decompressed_message = zlib.decompress(extracted_data)
                    decrypted_message = decrypt_message(decompressed_message, key)
                    return decrypted_message.decode('utf-8', errors='replace')
                except zlib.error as e:
                    raise ValueError(f"Decompression failed: {str(e)}")
                except Exception as e:
                    raise ValueError(f"Decryption failed: {str(e)}")
        
        # If we get here, no end marker was found
        raise ValueError("No hidden message found in the image")
        
    except Exception as e:
        raise ValueError(f"Error extracting message: {str(e)}")
