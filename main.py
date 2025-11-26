from PIL import Image
import numpy as np
import pyperclip
import os
import tkinter as tk
from tkinter import filedialog
from PIL import ImageGrab
from collections import deque
from scipy.ndimage import *
useNormalSize = False
useMaxSize = False
useNanochatSize = False
filename = ""
TESTMODE = False
DEBUG_DIR = "debug imagies"

def remove_background_and_crop(pil_img, green_component_min_size=5):
    img = np.array(pil_img.convert("RGB"))
    h, w = img.shape[:2]

    # --- Step 1: green detection ---
    R = img[:, :, 0].astype(float)
    G = img[:, :, 1].astype(float)
    B = img[:, :, 2].astype(float)
    green_mask = ((G / (np.maximum(R, B) + 1)) > 1.2).astype(np.uint8)

    # Optional: keep only the largest green component (removes isolated specks/small blobs).
    # This assumes the sprite interior is the largest connected green region.
    if green_component_min_size and green_component_min_size > 0:
        if TESTMODE:print(f"Keeping only green components >= {green_component_min_size} pixels")
        try:
            labels, num = label(green_mask)
            if TESTMODE:print(f"Found {num} green components")
            if num > 0:
                counts = np.bincount(labels.ravel())
                # Find the largest component
                largest_label = np.argmax(counts[1:]) + 1  # +1 because 0 is background
                largest_size = counts[largest_label]
                if TESTMODE:
                    print(f"Largest component size: {largest_size}")
                    print(f"All component sizes: {sorted(counts[1:], reverse=True)}")
                
                # Keep only components >= min_size
                keep = np.zeros_like(green_mask, dtype=bool)
                removed_count = 0
                for lab in range(1, num+1):
                    if counts[lab] >= green_component_min_size:
                        keep |= (labels == lab)
                    else:
                        removed_count += 1
                if TESTMODE:print(f"Removed {removed_count} small components")
                removed = green_mask.astype(bool) & (~keep)
                green_mask = keep.astype(np.uint8)
                if TESTMODE:
                    os.makedirs(DEBUG_DIR, exist_ok=True)
                    Image.fromarray((green_mask * 255).astype(np.uint8), mode="L").save(os.path.join(DEBUG_DIR, f"green_mask_filtered_{green_component_min_size}.png"))
                    Image.fromarray((removed.astype(np.uint8) * 255).astype(np.uint8), mode="L").save(os.path.join(DEBUG_DIR, f"green_removed_specks_{green_component_min_size}.png"))
        except Exception as e:
            if TESTMODE:print(f"Green filtering failed: {e}")
            pass

    # --- Step 2: detect outermost green pixels ---
    padded = np.pad(green_mask, 1, mode='constant', constant_values=0)
    outer_border = np.zeros_like(green_mask, dtype=np.uint8)
    for y in range(1, h+1):
        for x in range(1, w+1):
            if padded[y, x] == 1:
                neighborhood = padded[y-1:y+2, x-1:x+2]
                if np.any(neighborhood == 0):
                    outer_border[y-1, x-1] = 1
    
    # --- Step 3: alpha mask ---
    spritemask = binary_fill_holes(outer_border)
    spritemask = binary_erosion(spritemask, iterations=3)
    
    
    
    originalImage = Image.fromarray(img, mode="RGB")
    spritemask = spritemask.astype(np.uint8) * 255  # convert BEFORE PIL, ensures uint8
    spritemask = spritemask.squeeze()
    spritemask = np.ascontiguousarray(spritemask)
    Spritemask = Image.fromarray(spritemask, mode="L")
    originalImage.putalpha(Spritemask)
    rgba = np.array(originalImage)
    alpha = rgba[..., 3]               # take only RGB
    # Find all non-transparent pixels
    ys, xs = np.where(alpha > 0)

    if ys.size == 0 or xs.size == 0:
        # Entire image is transparent—return original?
        return rgba

    ymin, ymax = ys.min(), ys.max()
    xmin, xmax = xs.min(), xs.max()

    cropped = rgba[ymin:ymax+1, xmin:xmax+1]
    alpha = cropped[..., 3]                   
    transparent_mask = (alpha == 0)             
    cropped[..., :3][transparent_mask] = 255     
    return Image.fromarray(cropped, mode="RGBA")
   
def downscale_mode(img, target_size):
    if TESTMODE:print(target_size)
    if TESTMODE:print(img)
    img = img.resize(target_size, Image.NEAREST)
    if TESTMODE:print(img)
    return img

def brigthniss_increase(image):
    image = image.convert("RGB")
    data = image.getdata()
    
    newData = []
    for i in data:
        r,g,b = i
        r = int(r * 1.2)
        g = int(g * 1.2)
        b = int(b * 1.2)
        if r > 255:
            r = 255
        if g > 255:
            g = 255
        if b > 255:
            b = 255
        newData.append((r,g,b))
    image.putdata(newData)
    return image

def createImage(filename):
    global useMaxSize
    if isinstance(filename, str):
        image = Image.open(filename)
    elif isinstance(filename, Image.Image):
        image = filename
    else:
        if TESTMODE:print("Invalid image input")
        return
    if useMaxSize:
        pageDimensions = 42
        if TESTMODE:print("Page Dimision:",pageDimensions)
    if useNanochatSize:
        pageDimensions = 27
        if TESTMODE:print("Page Dimision:",pageDimensions)
    if useNormalSize:
        pageDimensions = 25
        if TESTMODE:print("Page Dimision:",pageDimensions)
        
    def adjustSize(image, pageDimensions):
        if pageDimensions == 27:
            size =[27,int(27*0.55)]
            if TESTMODE:print("size is now =",size)
        else:
            if TESTMODE:print(pageDimensions)
            size =[]
            for i in range(pageDimensions):
                newSize = [i]
                newSize.append(int(0.55*(image.height * newSize[0] / image.width)))
                
                # More accurate character prediction for optimized BBcode
                # Average: ~10 chars per pixel (includes color tags + newlines)
                total_pixels = newSize[0] * newSize[1]
                newlines = newSize[1]
                # Estimate: 10 chars per pixel + 1 char per newline
                predictedSize = total_pixels * 10 + newlines * 1
                
                if predictedSize < 10000:
                    size = newSize 
                if TESTMODE:print("size is now =",size)

        
        if TESTMODE:print(size)
        return downscale_mode(image, size)

    def getPixels(image):
        image = image.convert("RGB")
        return list(image.getdata())
    
    def rgb_to_hex(rgb):
        return "#{:02x}{:02x}{:02x}".format(*rgb)

    image = remove_background_and_crop(image)
    image.save("debug imagies/1.bg_removed_cropped_image.png")
    image = adjustSize(image, pageDimensions)
    image.save("debug imagies/2.resized_image.png")
    image = brigthniss_increase(image)
    image.save("debug imagies/3.Fully_processed_image.png")
    
    
    

    
    NAMED_COLORS = {
        (255,255,255): "white",
        (0,0,0): "black",
        (255,0,0): "red",
        (0,255,0): "lime",
        (0,0,255): "blue",
        (255,255,0): "yellow",
        (255,0,255): "magenta",
        (0,255,255): "cyan",
        (128,0,0): "maroon",
        (0,128,0): "green",
        (0,0,128): "navy",
        (128,128,0): "olive",
        (128,0,128): "purple",
        (0,128,128): "teal",
        (192,192,192): "silver",
        (128,128,128): "gray",
    }

    output = ""
    prev_color = None
    hex_cache = {}
    pixels = getPixels(image)

    for i, rgb in enumerate(pixels):
        # Determine color name
        if rgb == (255, 255, 255):
            color_name = "white"
        elif rgb in NAMED_COLORS:
            color_name = NAMED_COLORS[rgb]
        elif rgb in hex_cache:
            color_name = hex_cache[rgb]
        else:
            color_name = rgb_to_hex(rgb)
            hex_cache[rgb] = color_name
        
        # Check if next pixel has a different color
        next_pixel_idx = i + 1
        is_last_pixel = (next_pixel_idx % image.width == 0)
        
        if is_last_pixel:
            # Last pixel in row
            next_color = None
        else:
            # Look ahead to next pixel's color
            next_rgb = pixels[next_pixel_idx]
            if next_rgb == (255, 255, 255):
                next_color = "white"
            elif next_rgb in NAMED_COLORS:
                next_color = NAMED_COLORS[next_rgb]
            elif next_rgb in hex_cache:
                next_color = hex_cache[next_rgb]
            else:
                next_color = rgb_to_hex(next_rgb)
                hex_cache[next_rgb] = next_color
        
        # Output color tag only if color changed
        if color_name != prev_color:
            output += f"[color={color_name}]"
            prev_color = color_name
        
        output += "█"
        
        # Close color tag only if next pixel has different color (or end of line)
        if next_color != color_name:
            output += "[/color]"
            prev_color = None
        
        # End of line
        if is_last_pixel:
            output += "\n"
            prev_color = None  # reset at line break



    pyperclip.copy(output)
    if TESTMODE:print("Copied to clipboard")
def open_file():
    global filename
    filename = filedialog.askopenfilename()
    if TESTMODE:print("Selected file:", filename)
switch = False
def switchOn():
    global switch
    switch = not switch
    if switch:
        btnAutoMode.config(font=("Arial", 10), bg="Darkgreen", fg="black", relief="flat")
        check_clipboard()
    else:
        btnAutoMode.config(font=("Arial", 10), bg="darkgray", fg="black", relief="flat") 
def selectNormalSize():
    global useNormalSize, useMaxSize, useNanochatSize
    useNormalSize = True
    useMaxSize = False
    useNanochatSize = False
    btnSizeConfigNormalSize.config(font=("Arial", 10), bg="DarkGreen", fg="black",relief="flat")
    btnSizeConfigMaxSize.config(font=("Arial", 10), bg="DarkGray", fg="black",relief="flat")
    btnSizeConfigNanochatSize.config(font=("Arial", 10), bg="DarkGray", fg="black",relief="flat")
    
def selectMaxSize():
    global useNormalSize, useMaxSize, useNanochatSize
    useMaxSize = True
    useNormalSize = False
    useNanochatSize = False
    btnSizeConfigMaxSize.config(font=("Arial", 10), bg="DarkGreen", fg="black",relief="flat")
    btnSizeConfigNormalSize.config(font=("Arial", 10), bg="DarkGray", fg="black",relief="flat")
    btnSizeConfigNanochatSize.config(font=("Arial", 10), bg="DarkGray", fg="black",relief="flat")
def selectNanochatSize():
    global useNormalSize, useMaxSize, useNanochatSize
    useNanochatSize = True
    useNormalSize = False
    useMaxSize = False
    btnSizeConfigNanochatSize.config(font=("Arial", 10), bg="DarkGreen", fg="black",relief="flat")
    btnSizeConfigNormalSize.config(font=("Arial", 10), bg="DarkGray", fg="black",relief="flat")
    btnSizeConfigMaxSize.config(font=("Arial", 10), bg="DarkGray", fg="black",relief="flat")
def check_clipboard():
    global switch
    if switch:
        try:
            image = ImageGrab.grabclipboard()
            if isinstance(image, Image.Image):
                if TESTMODE:print(image)
                createImage(image)
        except Exception as e:
            if TESTMODE:print(f"Error: {e}")
        root.after(1000, check_clipboard)  # Check every second
if not TESTMODE:
    root = tk.Tk()
    root.title("Image to BBcode")
    root.geometry("400x500")
    root.config(bg="black",)
    btnFileSelect = tk.Button(root, text="Open Image", command=open_file,)
    btnFileSelect.config(font=("Arial", 10), bg="darkgray", fg="black",relief="flat")
    btnFileSelect.place(x=70,y=100,width=260,height=45)
    btnConvert = tk.Button(root, text="Convert", command=lambda: createImage(filename))
    btnConvert.config(font=("Arial", 10), bg="darkgray", fg="black",relief="flat")
    btnConvert.place(x=70,y=150,width=260,height=45)
    btnAutoMode = tk.Button(root, text="Auto Convert From Clipboard", command=lambda: switchOn())
    btnAutoMode.config(font=("Arial", 10), bg="darkgray", fg="black",relief="flat")
    btnAutoMode.place(x=70,y=200,width=260,height=45)

    btnSizeConfigNormalSize = tk.Button(root, text="Normal Size", command=lambda:selectNormalSize())
    btnSizeConfigNormalSize.config(font=("Arial", 10), bg="DarkGrey", fg="black",relief="flat")
    btnSizeConfigNormalSize.place(x=5,y=250,width=126.6,height=45)

    btnSizeConfigMaxSize = tk.Button(root, text="Maximum Size", command=lambda:selectMaxSize() )
    btnSizeConfigMaxSize.config(font=("Arial", 10), bg="DarkGrey", fg="black",relief="flat")
    btnSizeConfigMaxSize.place(x=136,y=250,width=126.6,height=45)

    btnSizeConfigNanochatSize = tk.Button(root, text="Nanochat Size", command=lambda:selectNanochatSize())
    btnSizeConfigNanochatSize.config(font=("Arial", 10), bg="DarkGrey", fg="black",relief="flat")
    btnSizeConfigNanochatSize.place(x=267,y=250,width=126.6,height=45)


    def on_close():
        if TESTMODE:print("Window is closing!")
        global switch
        switch = False
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
else:
    # TESTMODE operation
    useMaxSize = True
    test_image_path = "test_image.png"
    if TESTMODE:print("Running in TESTMODE with image:", test_image_path)
    createImage(test_image_path)