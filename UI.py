import tkinter as tk
from tkinter import filedialog
from PIL import ImageGrab, Image
from Image_Rendering import (
    create_image,
    TESTMODE,
    useNormalSize,
    useMaxSize,
    useNanochatSize,
)
filename = ""
auto_convert_enabled = False
def open_file():
    global filename
    filename = filedialog.askopenfilename()
    if filename:
        print("Selected:", filename)
def select_normal_size():
    global useNormalSize, useMaxSize, useNanochatSize
    useNormalSize = True
    useMaxSize = False
    useNanochatSize = False
    update_buttons()
def select_max_size():
    global useNormalSize, useMaxSize, useNanochatSize
    useMaxSize = True
    useNormalSize = False
    useNanochatSize = False
    update_buttons()
def select_nanochat_size():
    global useNormalSize, useMaxSize, useNanochatSize
    useNanochatSize = True
    useMaxSize = False
    useNormalSize = False
    update_buttons()


def update_buttons():
    btnNormal.config(bg="darkgreen" if useNormalSize else "darkgray")
    btnMax.config(bg="darkgreen" if useMaxSize else "darkgray")
    btnNano.config(bg="darkgreen" if useNanochatSize else "darkgray")
def toggle_auto_convert():
    global auto_convert_enabled
    auto_convert_enabled = not auto_convert_enabled

    btnAuto.config(bg="darkgreen" if auto_convert_enabled else "darkgray")

    if auto_convert_enabled:
        check_clipboard()
def check_clipboard():
    if not auto_convert_enabled:
        return
    try:
        img = ImageGrab.grabclipboard()
        if isinstance(img, Image.Image):
            create_image(img)
    except Exception as e:
        print("Clipboard error:", e)
    root.after(1000, check_clipboard)

root = tk.Tk()
root.title("Image to BBCode")
root.config(bg="black")
root.geometry("400x500")

btnOpen = tk.Button(root, text="Open Image", command=open_file, bg="darkgray")
btnOpen.place(x=70, y=100, width=260, height=45)

btnConvert = tk.Button(root, text="Convert", command=lambda: create_image(filename), bg="darkgray")
btnConvert.place(x=70, y=150, width=260, height=45)

btnAuto = tk.Button(root, text="Auto Convert From Clipboard", command=toggle_auto_convert, bg="darkgray")
btnAuto.place(x=70, y=200, width=260, height=45)

btnNormal = tk.Button(root, text="Normal Size", command=select_normal_size, bg="darkgray")
btnNormal.place(x=5, y=250, width=126, height=45)

btnMax = tk.Button(root, text="Maximum Size", command=select_max_size, bg="darkgray")
btnMax.place(x=136, y=250, width=126, height=45)

btnNano = tk.Button(root, text="Nanochat Size", command=select_nanochat_size, bg="darkgray")
btnNano.place(x=267, y=250, width=126, height=45)


# ---------------------------
# Entry Point
# ---------------------------

def run_gui():
    """Start the Tkinter main loop."""
    root.mainloop()
