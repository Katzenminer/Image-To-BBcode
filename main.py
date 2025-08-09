from PIL import Image
import pyperclip
import tkinter as tk
from tkinter import filedialog
from PIL import ImageGrab
useMaxSize = False
filename = ""
def createImage(filename):
    global useMaxSize
    if isinstance(filename, str):
        image = Image.open(filename)
    elif isinstance(filename, Image.Image):
        image = filename
    else:
        print("Invalid image input")
        return
    if useMaxSize:
        pageDimensions = 42
    else:
        pageDimensions = 25
    block = ["█"]
    def adjustSize(image, pageDimensions):
        size =[]
        for i in range(pageDimensions):
            newSize = [i]
            newSize.append(int(0.55*(image.height * newSize[0] / image.width)))
            predictedSize = (newSize[0] * newSize[1]*len("[color=#abcde4]█")) + (newSize[1] * len("[color=#000]\n"))
            if predictedSize < 10000:
                size = newSize 
            print("size is now =",size)
                
        return image.resize(size,Image.Resampling.NEAREST)

    def getPixels(image):
        pixels = []
        
        for y in range(image.height):
            for x in range(image.width):
                pixels.append(image.convert("RGB").getpixel([x,y]))

            
        return pixels
    def rgb_to_hex(rgb):

        return"#{:02x}{:02x}{:02x}".format(*rgb)

    image = adjustSize(image, pageDimensions)
    output = ""
    width = image.width
    for i, rgb in enumerate(getPixels(image)):
        hexcode = rgb_to_hex(rgb)
        output += f"[color={hexcode}]█"
        if (i + 1) % width == 0:
            output += "[color=#000]\n"
    pyperclip.copy(output)
    print("Copied to clipboard")
def open_file():
    global filename
    filename = filedialog.askopenfilename()
    print("Selected file:", filename)
switch = False
def switchOn():
    global switch
    switch = not switch
    if switch:
        btnAutoMode.config(font=("Arial", 10), bg="Darkgreen", fg="black", relief="flat")
        check_clipboard()
    else:
        btnAutoMode.config(font=("Arial", 10), bg="darkgray", fg="black", relief="flat") 
def sizeswitch():
    global useMaxSize
    useMaxSize = not useMaxSize
    if useMaxSize:
        btnSizeConfig.config(text=" Max Size")
    else:
        btnSizeConfig.config(text=" Normal Size",)        
def check_clipboard():
    global switch
    if switch:
        try:
            image = ImageGrab.grabclipboard()
            if isinstance(image, Image.Image):
                print(image)
                createImage(image)
        except Exception as e:
            print(f"Error: {e}")
        root.after(1000, check_clipboard)  # Check every second
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
btnSizeConfig = tk.Button(root, text="Normal Size", command=lambda: sizeswitch())
btnSizeConfig.config(font=("Arial", 10), bg="DarkGrey", fg="black",relief="flat")
btnSizeConfig.place(x=70,y=250,width=260,height=45)
def on_close():
    print("Window is closing!")
    global switch
    switch = False
    root.destroy()
root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()