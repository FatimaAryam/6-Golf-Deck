from PIL import Image
import os

def load_card_images(images_folder, size=(100, 140)):  # Set default size
    card_images = {}
    suits = ['C', 'D', 'H', 'S']
    ranks = [str(n) for n in range(2, 11)] + ['J', 'Q', 'K', 'A']

    for suit in suits:
        for rank in ranks:
            card_name = f"{rank}{suit}"
            image_path = os.path.join(images_folder, f"{card_name}.png")
            card_image = Image.open(image_path)
            card_image = card_image.resize(size, Image.LANCZOS)  # Resize image
            card_images[card_name] = card_image

    # Load back image
    back_image_path = os.path.join(images_folder, "red_back.png")
    back_image = Image.open(back_image_path)
    back_image = back_image.resize(size, Image.LANCZOS)  # Resize back image
    card_images["back"] = back_image

    return card_images

# Example usage
if __name__ == "__main__":
    images_folder = r"D:\Dell\Data\Fiverr\6_Golf_Card\6-Golf-Deck\images"  # Use raw string
    card_images = load_card_images(images_folder)
    print("Loaded card images:", card_images.keys())
