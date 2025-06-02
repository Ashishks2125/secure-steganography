import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, hashes, hmac
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag, InvalidKey
import os
import base64

def derive_key(key, salt=None):
    """Derive a secure key from the input key using PBKDF2."""
    if salt is None:
        salt = os.urandom(16)  # New salt for each encryption
    
    if isinstance(key, str):
        key = key.encode('utf-8')
    
    # Use PBKDF2 to derive a secure key
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 32 bytes = 256 bits for AES-256
        salt=salt,
        iterations=100000,  # High iteration count for security
        backend=default_backend()
    )
    
    derived_key = kdf.derive(key)
    return derived_key, salt

def encrypt_message(message, key):
    """
    Encrypt a message using AES-256-CBC with PKCS7 padding.
    
    Args:
        message: The message to encrypt (str or bytes)
        key: The encryption key (str or bytes)
        
    Returns:
        bytes: Encrypted data with format: salt (16 bytes) + iv (16 bytes) + encrypted data
    """
    try:
        # Convert message to bytes if it's a string
        if isinstance(message, str):
            message = message.encode('utf-8')
        
        # Derive a secure key and get the salt
        salt = os.urandom(16)
        derived_key, _ = derive_key(key, salt)
        
        # Generate a random 16-byte IV
        iv = os.urandom(16)
        
        # Create a cipher object with the key and IV
        cipher = Cipher(
            algorithms.AES(derived_key),
            modes.CBC(iv),
            backend=default_backend()
        )
        
        # Pad the message to be a multiple of the block size
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(message) + padder.finalize()
        
        # Encrypt the data
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        
        # Return salt + IV + encrypted data
        return salt + iv + encrypted
        
    except Exception as e:
        raise ValueError(f"Encryption failed: {str(e)}")

def decrypt_message(encrypted_data, key):
    """
    Decrypt a message using AES-256-CBC with PKCS7 padding.
    
    Args:
        encrypted_data: The encrypted data (bytes)
        key: The decryption key (str or bytes)
        
    Returns:
        bytes: The decrypted message
        
    Raises:
        ValueError: If decryption fails (invalid key, corrupted data, etc.)
    """
    try:
        if len(encrypted_data) < 32:  # 16 (salt) + 16 (IV)
            raise ValueError("Invalid encrypted data: too short")
        
        # Extract salt (first 16 bytes), IV (next 16 bytes), and encrypted data
        salt = encrypted_data[:16]
        iv = encrypted_data[16:32]
        encrypted = encrypted_data[32:]
        
        # Derive the key using the salt
        derived_key, _ = derive_key(key, salt)
        
        # Create a cipher object with the derived key and IV
        cipher = Cipher(
            algorithms.AES(derived_key),
            modes.CBC(iv),
            backend=default_backend()
        )
        
        # Decrypt the data
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted) + decryptor.finalize()
        
        # Unpad the data
        unpadder = padding.PKCS7(128).unpadder()
        try:
            data = unpadder.update(padded_data) + unpadder.finalize()
            # Try to decode as UTF-8, return bytes if it fails
            try:
                return data.decode('utf-8')
            except UnicodeDecodeError:
                return data
                
        except ValueError as e:
            # If unpadding fails, the key is probably wrong
            raise ValueError("Invalid key or corrupted data")
            
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")
