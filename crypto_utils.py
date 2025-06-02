import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

def encrypt_message(message, key):
    """
    Encrypt a message using AES-256-CBC.
    
    Args:
        message: The message to encrypt (str or bytes)
        key: The encryption key (bytes)
        
    Returns:
        bytes: The encrypted message with IV prepended
    """
    # Ensure key is 32 bytes
    key = key[:32]
    
    # Ensure message is bytes
    if isinstance(message, str):
        message = message.encode('utf-8')
    elif not isinstance(message, bytes):
        raise TypeError("Message must be str or bytes")
    
    # Generate a random IV
    iv = os.urandom(16)
    
    # Pad the message
    padder = padding.PKCS7(128).padder()
    padded_message = padder.update(message) + padder.finalize()
    
    # Encrypt the message
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_message = encryptor.update(padded_message) + encryptor.finalize()
    
    # Return IV + encrypted message
    return iv + encrypted_message

def decrypt_message(encrypted_message, key):
    """
    Decrypt a message using AES-256-CBC.
    
    Args:
        encrypted_message: The encrypted message with IV (bytes)
        key: The decryption key (bytes)
        
    Returns:
        bytes: The decrypted message
        
    Raises:
        ValueError: If decryption fails
    """
    # Ensure key is 32 bytes
    key = key[:32]
    
    # Split IV and encrypted message
    if len(encrypted_message) < 17:  # 16 for IV + at least 1 byte of data
        raise ValueError("Invalid encrypted message format")
        
    iv = encrypted_message[:16]
    encrypted_message = encrypted_message[16:]
    
    # Decrypt the message
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    
    try:
        decrypted_padded_message = decryptor.update(encrypted_message) + decryptor.finalize()
        
        # Unpad the message
        unpadder = padding.PKCS7(128).unpadder()
        decrypted_message = unpadder.update(decrypted_padded_message) + unpadder.finalize()
        
        return decrypted_message
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")
