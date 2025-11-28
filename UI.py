import tkinter as tk
from tkinter import filedialog
from PIL import ImageGrab, Image, ImageTk
import tkinter.font as tkFont
import Image_Rendering as IR
from Image_Rendering import create_image
filename = ""
auto_convert_enabled = False
def open_file():
    global filename
    filename = filedialog.askopenfilename()
    if filename:
        print("Selected:", filename)
def select_normal_size():
    IR.useNormalSize = True
    IR.useMaxSize = False
    IR.useNanochatSize = False
    update_buttons()
def select_max_size():
    IR.useMaxSize = True
    IR.useNormalSize = False
    IR.useNanochatSize = False
    update_buttons()
def select_nanochat_size():
    IR.useNanochatSize = True
    IR.useMaxSize = False
    IR.useNormalSize = False
    update_buttons()
def enable_border_cropping():
    IR.crop_to_border = not IR.crop_to_border
    update_buttons()
def update_buttons():
    btnNormal.config(bg="darkgreen" if IR.useNormalSize else "darkgray")
    btnMax.config(bg="darkgreen" if IR.useMaxSize else "darkgray")
    btnNano.config(bg="darkgreen" if IR.useNanochatSize else "darkgray")
    btnGreenBorderSensetiv.config(bg="darkgreen" if IR.crop_to_border else "darkgray")
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
myFont = tkFont.Font(family="Arial", size=14, weight="bold")
root.title("Image to BBCode")
root.config(bg="black")
root.geometry("400x500")
backround_img = Image.open("backround_space.png")
backround_img = backround_img.resize((400,500))
tk_backround_img = ImageTk.PhotoImage(backround_img)
backround = tk.Label(root, image=tk_backround_img)
backround.pack()



btnOpen = tk.Button(root, text="Open Image", command=open_file, compound="center",font=myFont,borderwidth=0,bg="darkgray")
btnOpen.pack()
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

btnGreenBorderSensetiv = tk.Button(root, text="Crop to and Remove Green Border", command=enable_border_cropping, bg="darkgray")
btnGreenBorderSensetiv.place(x=68, y=300, width=260, height=45)

# ---------------------------
# Entry Point
# ---------------------------

def run_gui():
    """Start the Tkinter main loop."""
    root.mainloop()
