import os
import numpy as np
from PIL import Image
from scipy.ndimage import label, center_of_mass, binary_fill_holes, binary_erosion
import pyperclip
TESTMODE = False
DEBUG_DIR = "debug images"
named_colors = {
    (255, 255, 255): "white",
    (0, 0, 0): "black",
    (255, 0, 0): "red",
    (0, 255, 0): "lime",
    (0, 0, 255): "blue",
    (255, 255, 0): "yellow",
    (0, 255, 255): "cyan",
    (128, 0, 0): "maroon",
    (0, 128, 0): "green",
    (0, 0, 128): "navy",
    (128, 128, 0): "olive",
    (128, 0, 128): "purple",
    (0, 128, 128): "teal",
    (192, 192, 192): "silver",
    (128, 128, 128): "gray",
}
useNormalSize = False
useMaxSize = False
useNanochatSize = False
crop_to_border = False
def detect_green(img_array):
    r = img_array[:, :, 0].astype(float)
    g = img_array[:, :, 1].astype(float)
    b = img_array[:, :, 2].astype(float)
    return ((g / (np.maximum(r, b) + 1)) > 1.2).astype(np.uint8)
def speck_cleanup(pil_img):
    img = np.array(pil_img)
    green_mask = detect_green(img)

    def keep_specks(mask, max_size=5, min_dist=10):
        h, w = mask.shape
        labeled, num = label(mask)
        if num == 0:
            return np.zeros_like(mask)

        cx, cy = w / 2, h / 2
        output = np.zeros_like(mask, dtype=bool)

        for lbl in range(1, num + 1):
            blob = (labeled == lbl)
            size = blob.sum()
            by, bx = center_of_mass(blob)
            dist = np.hypot(bx - cx, by - cy)

            if size <= max_size and dist >= min_dist:
                output[blob] = True

        return output.astype(np.uint8)

    cleaned = keep_specks(green_mask)
    cleaned *= 255

    # Turn cleaned specks white
    img_copy = np.array(pil_img).copy()
    img_copy[cleaned == 255] = [255, 255, 255]
    return Image.fromarray(img_copy, mode="RGB")


# ---------------------------
# BBCode Length Estimation
# ---------------------------

def predict_bbcode_length(image, width):
    image = image.convert("RGB")
    pixels = list(image.getdata())

    def rgb_name(rgb):
        return named_colors.get(rgb, "#{:02x}{:02x}{:02x}".format(*rgb))

    total = 0
    prev_color = None

    for i, rgb in enumerate(pixels):
        color = rgb_name(rgb)

        if color != prev_color:
            total += len(f"[color={color}]")
            prev_color = color

        total += 1  # █

        end_row = ((i + 1) % width == 0)
        if end_row:
            total += len("[/color]") + 1
            prev_color = None
        else:
            next_color = rgb_name(pixels[i + 1])
            if next_color != color:
                total += len("[/color]")
                prev_color = None

    return total
def remove_background_and_crop(pil_img, min_size=5):
    img = np.array(pil_img.convert("RGB"))
    green_mask = detect_green(img)

    # Detect border pixels touching non-green
    h, w = green_mask.shape
    padded = np.pad(green_mask, 1, constant_values=0)
    border = np.zeros_like(green_mask, dtype=np.uint8)

    for y in range(1, h + 1):
        for x in range(1, w + 1):
            if padded[y, x] == 1 and np.any(padded[y - 1:y + 2, x - 1:x + 2] == 0):
                border[y - 1, x - 1] = 1

    sprite_mask = binary_fill_holes(border)
    sprite_mask = binary_erosion(sprite_mask, iterations=3)
    sprite_mask = (sprite_mask.astype(np.uint8) * 255)

    # Apply alpha mask
    image_rgba = pil_img.convert("RGBA")
    image_rgba.putalpha(Image.fromarray(sprite_mask, mode="L"))

    arr = np.array(image_rgba)
    alpha = arr[..., 3]

    ys, xs = np.where(alpha > 0)
    if ys.size == 0 or xs.size == 0:
        return image_rgba

    y_min, y_max = ys.min(), ys.max()
    x_min, x_max = xs.min(), xs.max()

    cropped = arr[y_min:y_max + 1, x_min:x_max + 1]
    cropped[..., :3][cropped[..., 3] == 0] = 255

    return Image.fromarray(cropped, mode="RGBA")
def downscale_mode(img, size):
    return img.resize(size, Image.NEAREST)


# ---------------------------
# Main Image Pipeline
# ---------------------------

def create_image(image_input):
    global useMaxSize, useNormalSize, useNanochatSize,crop_to_border

    # Load image
    image = image_input if isinstance(image_input, Image.Image) else Image.open(image_input)

    # Page width mode
    if useMaxSize:
        page_width = 43
    elif useNanochatSize:
        page_width = 27
    else:
        page_width = 25

    # Resize logic
    def choose_size(raw, max_w):
        if max_w == 27:
            return [27, int(27 * 0.55)]

        chosen = []
        for w in range(1, max_w):
            h = int(raw.height * (w / raw.width) * 0.55)
            if h <= 0:
                continue

            if predict_bbcode_length(raw.resize((w, h), Image.NEAREST), w) <= 10000:
                chosen = [w, h]

        return chosen

    # Pipeline steps
    if crop_to_border:image = remove_background_and_crop(image)
    new_size = choose_size(image, page_width)
    image = downscale_mode(image, new_size)
    if crop_to_border:image = speck_cleanup(image.convert("RGB"))

    # Generate BBCode
    pixels = list(image.getdata())
    output = []
    prev_color = None
    hex_cache = {}

    def rgb_hex(rgb):
        return "#{:02x}{:02x}{:02x}".format(*rgb)

    width = image.width

    for i, rgb in enumerate(pixels):
        color = named_colors.get(rgb)
        if color is None:
            color = hex_cache.get(rgb)
            if color is None:
                color = rgb_hex(rgb)
                hex_cache[rgb] = color

        # Start color block
        if color != prev_color:
            output.append(f"[color={color}]")
            prev_color = color

        output.append("█")

        end_row = ((i + 1) % width == 0)

        if end_row:
            output.append("[/color]\n")
            prev_color = None
            continue

        # Look ahead
        next_rgb = pixels[i + 1]
        next_color = named_colors.get(next_rgb) or hex_cache.get(next_rgb) or rgb_hex(next_rgb)

        if next_color != color:
            output.append("[/color]")
            prev_color = None

    # Copy result
    pyperclip.copy("".join(output))
    print("Copied to clipboard!")
