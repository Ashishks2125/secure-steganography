from dh_utils import get_user_input
from stego_utils import embed_message, extract_message

if __name__ == "__main__":
    image, mode, image_path, key = get_user_input()

    if image is not None:
        if mode == "1":
            message = input("Enter the message to hide: ").strip()
            output_path = input("Enter the output image name (with extension): ").strip()
            embed_message(image, message, key, output_path)
        elif mode == "2":
            extract_message(image, key)
        else:
            print("Invalid mode selected.")
