from Image_Rendering import TESTMODE, create_image
import UI

def main():
    if TESTMODE:
        print("Running in TESTMODE...")
        create_image("test_image.png")
    else:
        UI.run_gui()
if __name__ == "__main__":
    main()
