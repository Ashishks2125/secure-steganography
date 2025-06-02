import secrets
import hashlib
import cv2

P = 23  # Prime number (use a large safe prime for real apps)
G = 9   # Generator

def generate_private_key():
    return int(input(f"Enter your private key (an integer less than {P}): ").strip())

def generate_public_key(private_key):
    return pow(G, private_key, P)

def generate_shared_key(private_key, other_public_key):
    shared_secret = pow(other_public_key, private_key, P)
    return hashlib.sha256(str(shared_secret).encode()).digest()

def get_user_input():
    mode = input("Choose mode: (1) Encode, (2) Decode: ").strip()
    image_path = input("Enter the path of the image: ").strip()
    img = cv2.imread(image_path)

    if img is None:
        print("Error: Could not load image. Please check the path.")
        return None, None, None, None

    print("\n--- Diffie-Hellman Key Exchange ---")
    user_private = generate_private_key()
    user_public = generate_public_key(user_private)
    print("Your Public Key (share with the other user):", user_public)

    other_public = int(input("Enter the other user's public key: ").strip())
    shared_key = generate_shared_key(user_private, other_public)
    print("Shared AES key established via Diffie-Hellman.")

    return img, mode, image_path, shared_key
