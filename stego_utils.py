import cv2
import zlib
from crypto_utils import encrypt_message, decrypt_message

def text_to_binary(text):
    return ''.join(format(byte, '08b') for byte in text)

def binary_to_text(binary_data):
    byte_list = [binary_data[i:i+8] for i in range(0, len(binary_data), 8)]
    return bytes([int(b, 2) for b in byte_list])

def embed_message(img, message, key, output_path):
    encrypted_message = encrypt_message(message, key)
    compressed_message = zlib.compress(encrypted_message)
    binary_message = text_to_binary(compressed_message) + '1111111111111110'

    h, w, _ = img.shape
    total_pixels = h * w * 3 * 2

    if len(binary_message) > total_pixels:
        print("Error: Message too long to fit in the image.")
        return

    binary_index = 0
    for i in range(h):
        for j in range(w):
            for k in range(3):
                if binary_index < len(binary_message) - 1:
                    two_bits = binary_message[binary_index:binary_index+2]
                    img[i, j, k] = (img[i, j, k] & 0xFC) | int(two_bits, 2)
                    binary_index += 2
                else:
                    break

    cv2.imwrite(output_path, img)
    print(f"Message successfully encoded in {output_path}")

def extract_message(img, key):
    binary_message = ""
    h, w, _ = img.shape

    for i in range(h):
        for j in range(w):
            for k in range(3):
                binary_message += format(img[i, j, k], '08b')[-2:]

    end_marker = '1111111111111110'
    end_index = binary_message.find(end_marker)
    if end_index == -1:
        print("Error: No hidden message found.")
        return

    binary_message = binary_message[:end_index]
    extracted_data = binary_to_text(binary_message)

    try:
        decompressed_message = zlib.decompress(extracted_data)
        decrypted_message = decrypt_message(decompressed_message, key)
        print("\nExtracted Message:", decrypted_message)
    except Exception as e:
        print("Error: Unable to decrypt the message. Incorrect key?", e)
